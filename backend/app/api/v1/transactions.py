"""Transactions endpoints — supports filtering, pagination, CSV import/export."""
from __future__ import annotations
from app.api.deps import get_current_user
from app.db.models.user import User

import csv
import io
import re
import uuid
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


def _parse_date_safe(val: str) -> date:
    """Parse various date formats safely."""
    val = val.strip().strip("\"'")
    if not val:
        return date.today()
    
    # Try ISO YYYY-MM-DD
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y", "%d-%m-%Y", "%b %d, %Y", "%B %d, %Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(val.split("T")[0] if "T" in val else val, fmt).date()
        except Exception:
            continue
            
    # Fallback to date.fromisoformat if valid
    try:
        return date.fromisoformat(val[:10])
    except Exception:
        return date.today()


def _parse_amount_safe(val: str) -> float:
    """Strip currency symbols, commas, spaces and parse float."""
    cleaned = re.sub(r"[^\d.-]", "", str(val))
    if not cleaned or cleaned == "-" or cleaned == ".":
        return 0.0
    try:
        return float(cleaned)
    except Exception:
        return 0.0


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
        id=f"tx-custom-{uuid.uuid4().hex[:16]}",
        user_id=current_user.id,
        date=_parse_date_safe(data.date),
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
            setattr(tx, key, _parse_date_safe(value))
        else:
            setattr(tx, key, value)

    await db.flush()
    return _tx_to_response(tx)


@router.post("/import", response_model=CSVImportResult)
async def import_csv(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Import transactions from CSV text with automatic header detection and category resolution."""
    csv_text = (data.get("csvText") or data.get("csv_text") or "").strip()
    if not csv_text:
        return {"imported_count": 0, "importedCount": 0}

    # 1. Ensure user has an account to link transactions
    acc_res = await db.execute(
        select(Account).where(Account.user_id == current_user.id).limit(1)
    )
    account = acc_res.scalars().first()
    if not account:
        account = Account(
            id=f"acc-{uuid.uuid4().hex[:12]}",
            user_id=current_user.id,
            name="Primary Checking Account",
            type="checking",
            balance=245000.0,
            currency="INR",
            institution="Primary Bank",
            mask="4821",
            color="#3B82F6",
            is_active=True,
        )
        db.add(account)
        await db.flush()
    account_id = account.id

    # 2. Cache user categories for fast matching
    cat_res = await db.execute(select(Category).where(Category.user_id == current_user.id))
    user_cats = cat_res.scalars().all()
    
    # Lookup dictionaries
    cat_by_id = {c.id: c for c in user_cats}
    cat_by_name = {c.name.lower().strip(): c for c in user_cats}

    # 3. Parse CSV rows using robust csv.reader
    reader = csv.reader(io.StringIO(csv_text))
    rows = [row for row in reader if row and any(cell.strip() for cell in row)]
    if not rows:
        return {"imported_count": 0, "importedCount": 0}

    # Detect header mapping
    header_indices = {"date": 0, "merchant": 1, "amount": 2, "category": 3}
    first_row = [c.strip().lower() for c in rows[0]]
    has_header = False

    for idx, col in enumerate(first_row):
        if "date" in col:
            header_indices["date"] = idx
            has_header = True
        elif any(k in col for k in ("merchant", "payee", "description", "name")):
            header_indices["merchant"] = idx
            has_header = True
        elif any(k in col for k in ("amount", "total", "price", "val")):
            header_indices["amount"] = idx
            has_header = True
        elif any(k in col for k in ("cat", "tag", "type")):
            header_indices["category"] = idx
            has_header = True

    start_row = 1 if has_header else 0
    imported = 0

    for i in range(start_row, len(rows)):
        row = rows[i]
        if len(row) < 2:
            continue

        d_idx = header_indices["date"]
        m_idx = header_indices["merchant"]
        a_idx = header_indices["amount"]
        c_idx = header_indices["category"]

        date_val = row[d_idx] if d_idx < len(row) else ""
        merchant_val = row[m_idx] if m_idx < len(row) else "Imported Merchant"
        amount_val = row[a_idx] if a_idx < len(row) else "0.0"
        cat_val = row[c_idx] if c_idx < len(row) else "Other Expenses"

        parsed_date = _parse_date_safe(date_val)
        parsed_amount = _parse_amount_safe(amount_val)
        if parsed_amount == 0.0 and not amount_val.strip():
            continue

        # Resolve category
        clean_cat = cat_val.strip()
        matched_cat_id: str | None = None

        if clean_cat in cat_by_id:
            matched_cat_id = cat_by_id[clean_cat].id
        elif clean_cat.lower() in cat_by_name:
            matched_cat_id = cat_by_name[clean_cat.lower()].id
        else:
            # Check normalized name
            normalized_name = clean_cat.replace("cat-", "").replace("-", " ").replace("_", " ").title() or "Other Expenses"
            if normalized_name.lower() in cat_by_name:
                matched_cat_id = cat_by_name[normalized_name.lower()].id
            else:
                # Create a new Category for this user with guaranteed unique ID
                new_cat_id = f"cat-{uuid.uuid4().hex[:12]}"
                new_cat = Category(
                    id=new_cat_id,
                    user_id=current_user.id,
                    name=normalized_name,
                    icon="Tag",
                    color="#10B981",
                    type="expense",
                    monthly_budget=0.0,
                    default_monthly_budget=300.0,
                    is_custom=True,
                )
                db.add(new_cat)
                await db.flush()
                cat_by_id[new_cat_id] = new_cat
                cat_by_name[normalized_name.lower()] = new_cat
                matched_cat_id = new_cat_id

        tx_obj = Transaction(
            id=f"tx-imp-{uuid.uuid4().hex[:16]}",
            user_id=current_user.id,
            date=parsed_date,
            merchant=merchant_val.strip().strip("\"'") or "Imported Merchant",
            amount=parsed_amount,
            category_id=matched_cat_id,
            account_id=account_id,
            status="settled",
            is_recurring=False,
        )
        db.add(tx_obj)
        imported += 1

    await db.flush()
    return {"imported_count": imported, "importedCount": imported}


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
