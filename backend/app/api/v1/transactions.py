"""Transactions endpoints â€” supports filtering, pagination, CSV import/export."""
from __future__ import annotations
from app.api.deps import get_current_user
from app.db.models.user import User

import csv
import io
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.transaction import Transaction
from app.db.models.account import Account
from app.db.models.category import Category
from app.ml.anomaly.ml_detectors import EnhancedIsolationForest
from app.schemas.transaction import (
    TransactionResponse, TransactionCreate, TransactionUpdate,
    PaginatedTransactions, CSVImportResult,
)


router = APIRouter()


def _tx_to_response(tx: Transaction) -> dict:
    tags = tx.tags.split(",") if tx.tags else None
    return {
        "id": tx.id,
        "date": tx.date.isoformat() if isinstance(tx.date, date) else str(tx.date),
        "merchant": tx.merchant,
        "categoryId": tx.category_id or "",
        "accountId": tx.account_id,
        "amount": tx.amount,
        "status": tx.status,
        "isRecurring": tx.is_recurring,
        "isAnomaly": tx.is_anomaly if tx.is_anomaly else None,
        "anomalyReason": tx.anomaly_reason,
        "notes": tx.notes,
        "tags": tags,
    }


@router.get("", response_model=PaginatedTransactions)
async def get_transactions(
    search: str | None = None,
    categoryIds: str | None = None,  # comma-separated
    accountIds: str | None = None,  # comma-separated
    startDate: str | None = None,
    endDate: str | None = None,
    minAmount: float | None = None,
    maxAmount: float | None = None,
    anomalyOnly: bool | None = None,
    recurringOnly: bool | None = None,
    sortBy: str = "date",
    sortOrder: str = "desc",
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Transaction).where(Transaction.user_id == current_user.id)

    if search:
        term = f"%{search.lower()}%"
        query = query.where(
            or_(
                func.lower(Transaction.merchant).like(term),
                func.lower(Transaction.notes).like(term),
            )
        )

    if categoryIds:
        cat_list = [c.strip() for c in categoryIds.split(",") if c.strip()]
        if cat_list:
            query = query.where(Transaction.category_id.in_(cat_list))

    if accountIds:
        acc_list = [a.strip() for a in accountIds.split(",") if a.strip()]
        if acc_list:
            query = query.where(Transaction.account_id.in_(acc_list))

    if startDate:
        query = query.where(Transaction.date >= startDate)
    if endDate:
        query = query.where(Transaction.date <= endDate)

    if anomalyOnly:
        query = query.where(Transaction.is_anomaly == True)
    if recurringOnly:
        query = query.where(Transaction.is_recurring == True)

    if minAmount is not None:
        query = query.where(func.abs(Transaction.amount) >= minAmount)
    if maxAmount is not None:
        query = query.where(func.abs(Transaction.amount) <= maxAmount)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Sort
    if sortBy == "amount":
        order_col = func.abs(Transaction.amount)
    elif sortBy == "merchant":
        order_col = Transaction.merchant
    else:
        order_col = Transaction.date

    if sortOrder == "asc":
        query = query.order_by(asc(order_col), asc(Transaction.id))
    else:
        query = query.order_by(desc(order_col), desc(Transaction.id))

    # Paginate
    total_pages = max(1, -(-total // limit))
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    txs = result.scalars().all()

    return {
        "transactions": [_tx_to_response(tx) for tx in txs],
        "total": total,
        "page": page,
        "totalPages": total_pages,
    }


@router.post("", response_model=TransactionResponse, status_code=201)
async def add_transaction(data: TransactionCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    tx = Transaction(
        id=f"tx-custom-{int(datetime.utcnow().timestamp() * 1000)}",
        user_id=current_user.id,
        date=date.fromisoformat(data.date),
        merchant=data.merchant,
        category_id=data.category_id,
        account_id=data.account_id,
        amount=data.amount,
        status=data.status,
        is_recurring=data.is_recurring,
        is_anomaly=data.is_anomaly or False,
        anomaly_reason=data.anomaly_reason,
        notes=data.notes,
        tags=",".join(data.tags) if data.tags else None,
    )
    db.add(tx)
    await db.flush()
    return _tx_to_response(tx)


@router.patch("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: str,
    data: TransactionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id, Transaction.user_id == current_user.id
        )
    )
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    update_data = data.model_dump(exclude_unset=True, by_alias=False)
    for key, value in update_data.items():
        if key == "tags" and isinstance(value, list):
            setattr(tx, key, ",".join(value))
        elif key == "date" and isinstance(value, str):
            setattr(tx, key, date.fromisoformat(value))
        else:
            setattr(tx, key, value)

    await db.flush()
    return _tx_to_response(tx)


@router.post("/import", response_model=CSVImportResult)
async def import_csv(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Import transactions from CSV text."""
    csv_text = data.get("csvText", "")
    lines = csv_text.strip().split("\n")
    imported = 0
    
    # Ensure user has an account
    acc_res = await db.execute(select(Account).where(Account.user_id == current_user.id).limit(1))
    account = acc_res.scalars().first()
    if not account:
        account = Account(id=f"acc-{current_user.id[:8]}", user_id=current_user.id, name="Default Account", type="checking", balance=0.0, currency="USD")
        db.add(account)
        await db.flush()
    account_id = account.id

    # Cache valid categories
    cat_res = await db.execute(select(Category.id).where(Category.user_id == current_user.id))
    valid_categories = set(cat_res.scalars().all())

    for i, line in enumerate(lines):
        if i == 0:
            continue  # skip header
        parts = [p.strip().strip("\"'") for p in line.split(",")]
        if len(parts) >= 3:
            date_str, merchant_str, amount_str = parts[0], parts[1], parts[2]
            cat_str = parts[3] if len(parts) > 3 else "cat-other"
            try:
                amount = float(amount_str)
            except ValueError:
                continue
                
            # Ensure category exists
            if cat_str and cat_str not in valid_categories:
                new_cat = Category(
                    id=cat_str,
                    user_id=current_user.id,
                    name=cat_str.replace("cat-", "").replace("-", " ").title(),
                    type="expense",
                    is_custom=True
                )
                db.add(new_cat)
                valid_categories.add(cat_str)
                
            tx_obj = Transaction(
                id=f"tx-import-{int(datetime.utcnow().timestamp() * 1000)}-{i}",
                user_id=current_user.id,
                date=date.fromisoformat(date_str) if date_str else date.today(),
                merchant=merchant_str or "Imported Merchant",
                amount=amount,
                category_id=cat_str,
                account_id=account_id,
                status="settled",
                is_recurring=False,
            )
            db.add(tx_obj)
            imported += 1

    await db.flush()
    return {"imported_count": imported}


@router.get("/export", response_class=PlainTextResponse)
async def export_csv(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Export all transactions as CSV."""
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .order_by(desc(Transaction.date))
    )
    txs = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Merchant", "Amount", "Category", "Account", "Status", "Recurring"])
    for tx in txs:
        writer.writerow([
            tx.date.isoformat() if isinstance(tx.date, date) else str(tx.date),
            tx.merchant,
            tx.amount,
            tx.category_id,
            tx.account_id,
            tx.status,
            "Yes" if tx.is_recurring else "No",
        ])

    return PlainTextResponse(output.getvalue(), media_type="text/csv")


