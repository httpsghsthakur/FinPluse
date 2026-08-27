"""Admin endpoints — reset data, export, and CSV replace."""
from __future__ import annotations

import csv
import io
import re
import uuid
from datetime import datetime, date

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.account import Account
from app.db.models.transaction import Transaction
from app.db.models.category import Category
from app.db.models.goal import Goal
from app.db.models.insight import Insight
from app.db.models.recurring import RecurringTransaction
from app.api.deps import get_current_user
from app.services.seed_service import (
    generate_user,
    generate_accounts,
    generate_categories,
    generate_goals,
    generate_insights,
    generate_transactions,
    generate_recurring,
)

router = APIRouter()


def _parse_date_safe(val: str) -> date:
    val = val.strip().strip("\"'")
    if not val:
        return date.today()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y", "%d-%m-%Y", "%b %d, %Y"):
        try:
            return datetime.strptime(val.split("T")[0] if "T" in val else val, fmt).date()
        except Exception:
            continue
    try:
        return date.fromisoformat(val[:10])
    except Exception:
        return date.today()


def _parse_amount_safe(val: str) -> float:
    cleaned = re.sub(r"[^\d.-]", "", str(val))
    if not cleaned or cleaned == "-" or cleaned == ".":
        return 0.0
    try:
        return float(cleaned)
    except Exception:
        return 0.0


async def seed_database(db: AsyncSession, current_user: User = None) -> None:
    if current_user is None:
        current_user = User(id="00000000-0000-4000-a000-000000000001", email="alex.morgan@finpilot.ai", name="Alex Morgan")
        db.add(current_user)
        await db.flush()

    # Check if user already has categories
    cat_check = await db.execute(select(Category).where(Category.user_id == current_user.id).limit(1))
    if cat_check.scalars().first():
        return  # Already seeded for this user

    # Create categories
    for cat_data in generate_categories(current_user.id):
        cat = Category(
            id=cat_data["id"],
            user_id=current_user.id,
            name=cat_data["name"],
            icon=cat_data["icon"],
            color=cat_data["color"],
            type=cat_data["type"],
            monthly_budget=cat_data["monthly_budget"],
            default_monthly_budget=cat_data.get("default_monthly_budget", cat_data["monthly_budget"]),
            is_system=cat_data["is_system"],
            is_custom=cat_data["is_custom"],
        )
        db.add(cat)
    await db.flush()

    # Create accounts
    for acc_data in generate_accounts(current_user.id):
        acc = Account(
            id=acc_data["id"],
            user_id=current_user.id,
            name=acc_data["name"],
            type=acc_data["type"],
            balance=acc_data["balance"],
            currency=acc_data["currency"],
            institution=acc_data["institution"],
            mask=acc_data["mask"],
            color=acc_data["color"],
            is_active=acc_data["is_active"],
        )
        db.add(acc)
    await db.flush()

    # Create goals
    for goal_data in generate_goals(current_user.id):
        goal = Goal(
            id=goal_data["id"],
            user_id=current_user.id,
            name=goal_data["name"],
            target_amount=goal_data["target_amount"],
            current_amount=goal_data["current_amount"],
            deadline=_parse_date_safe(goal_data["deadline"]),
            category=goal_data["category"],
            linked_account_id=goal_data["linked_account_id"],
            monthly_contribution=goal_data["monthly_contribution"],
            color=goal_data["color"],
            icon=goal_data["icon"],
            is_completed=goal_data["is_completed"],
            boost_suggestion=goal_data.get("boost_suggestion"),
        )
        db.add(goal)
    await db.flush()

    # Create transactions
    for tx_data in generate_transactions(current_user.id):
        tx = Transaction(
            id=tx_data["id"],
            user_id=current_user.id,
            date=_parse_date_safe(tx_data["date"]),
            merchant=tx_data["merchant"],
            category_id=tx_data["category_id"],
            account_id=tx_data["account_id"],
            amount=tx_data["amount"],
            status=tx_data["status"],
            is_recurring=tx_data.get("is_recurring", False),
            is_anomaly=tx_data.get("is_anomaly", False),
            anomaly_reason=tx_data.get("anomaly_reason"),
            notes=tx_data.get("notes"),
        )
        db.add(tx)
    await db.flush()

    # Create recurring
    for rec_data in generate_recurring(current_user.id):
        rec = RecurringTransaction(
            id=rec_data["id"],
            user_id=current_user.id,
            merchant=rec_data["merchant"],
            category_id=rec_data["category_id"],
            account_id=rec_data["account_id"],
            is_recurring=rec_data["is_recurring"],
            frequency=rec_data["frequency"],
            expected_amount=rec_data["expected_amount"],
            amount_variance=rec_data["amount_variance"],
            expected_next_date=_parse_date_safe(rec_data["expected_next_date"]),
            confidence=rec_data["confidence"],
            last_seen_date=_parse_date_safe(rec_data["last_seen_date"]),
            occurrence_count=rec_data["occurrence_count"],
            is_active=rec_data["is_active"],
        )
        db.add(rec)
    await db.flush()

    # Create insights
    for ins_data in generate_insights(current_user.id):
        ins = Insight(
            id=ins_data["id"],
            user_id=current_user.id,
            title=ins_data["title"],
            description=ins_data["description"],
            severity=ins_data["severity"],
            type=ins_data["type"],
            date=_parse_date_safe(ins_data["date"]),
            is_dismissed=ins_data["is_dismissed"],
            why_explanation=ins_data["why_explanation"],
            grounded_data=ins_data["grounded_data"],
            action_label=ins_data.get("action_label"),
            action_path=ins_data.get("action_path"),
        )
        db.add(ins)
    await db.flush()


@router.post("/reset", status_code=204)
async def reset_all_data(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Reset all demo data to initial state."""
    await db.execute(delete(Transaction).where(Transaction.user_id == current_user.id))
    await db.execute(delete(RecurringTransaction).where(RecurringTransaction.user_id == current_user.id))
    await db.execute(delete(Insight).where(Insight.user_id == current_user.id))
    await db.execute(delete(Goal).where(Goal.user_id == current_user.id))
    await db.execute(delete(Account).where(Account.user_id == current_user.id))
    await db.execute(delete(Category).where(Category.user_id == current_user.id))
    await db.flush()

    # Re-seed with fresh data for this user
    await seed_database(db, current_user)


@router.get("/export")
async def export_all_data(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Export all data as JSON."""
    accs = (await db.execute(select(Account).where(Account.user_id == current_user.id))).scalars().all()
    cats = (await db.execute(select(Category).where(Category.user_id == current_user.id))).scalars().all()
    goals = (await db.execute(select(Goal).where(Goal.user_id == current_user.id))).scalars().all()
    txs = (await db.execute(
        select(Transaction).where(Transaction.user_id == current_user.id).order_by(Transaction.date.desc())
    )).scalars().all()
    recs = (await db.execute(select(RecurringTransaction).where(RecurringTransaction.user_id == current_user.id))).scalars().all()
    insights = (await db.execute(select(Insight).where(Insight.user_id == current_user.id))).scalars().all()

    return {
        "accounts": [{"id": a.id, "name": a.name, "type": a.type, "balance": a.balance, "currency": a.currency, "institution": a.institution, "mask": a.mask, "color": a.color, "lastSynced": a.last_synced.isoformat() if a.last_synced else "", "isActive": a.is_active} for a in accs],
        "categories": [{"id": c.id, "name": c.name, "icon": c.icon, "color": c.color, "type": c.type, "monthlyBudget": c.monthly_budget, "defaultMonthlyBudget": c.default_monthly_budget, "isSystem": c.is_system, "isCustom": c.is_custom} for c in cats],
        "goals": [{"id": g.id, "name": g.name, "targetAmount": g.target_amount, "currentAmount": g.current_amount, "deadline": g.deadline.isoformat() if isinstance(g.deadline, date) else str(g.deadline), "category": g.category, "linkedAccountId": g.linked_account_id, "monthlyContribution": g.monthly_contribution, "color": g.color, "icon": g.icon, "isCompleted": g.is_completed, "boostSuggestion": g.boost_suggestion} for g in goals],
        "transactions": [{"id": t.id, "date": t.date.isoformat() if isinstance(t.date, date) else str(t.date), "merchant": t.merchant, "categoryId": t.category_id, "accountId": t.account_id, "amount": t.amount, "status": t.status, "isRecurring": t.is_recurring, "isAnomaly": t.is_anomaly, "anomalyReason": t.anomaly_reason, "notes": t.notes} for t in txs],
        "recurring": [{"id": r.id, "merchant": r.merchant, "categoryId": r.category_id, "accountId": r.account_id, "isRecurring": r.is_recurring, "frequency": r.frequency, "expectedAmount": r.expected_amount, "expectedNextDate": r.expected_next_date.isoformat() if r.expected_next_date else None, "confidence": r.confidence, "isActive": r.is_active} for r in recs],
        "insights": [{"id": i.id, "title": i.title, "description": i.description, "severity": i.severity, "type": i.type, "date": i.date.isoformat() if i.date else "", "isDismissed": i.is_dismissed, "whyExplanation": i.why_explanation, "groundedData": i.grounded_data or [], "actionLabel": i.action_label, "actionPath": i.action_path} for i in insights],
    }


@router.post("/replace_transactions_from_csv", status_code=200)
async def replace_transactions_from_csv(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Wipes all transactions and loads them from CSV text with automatic category/account resolution."""
    csv_text = (data.get("csvText") or data.get("csv_text") or "").strip()
    if not csv_text:
        return {"importedCount": 0, "imported_count": 0}

    # 1. Ensure user has an account
    acc_res = await db.execute(select(Account).where(Account.user_id == current_user.id).limit(1))
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

    # 2. Wipe existing transactions
    await db.execute(delete(Transaction).where(Transaction.user_id == current_user.id))

    # 3. Cache categories
    cat_res = await db.execute(select(Category).where(Category.user_id == current_user.id))
    user_cats = cat_res.scalars().all()
    cat_by_id = {c.id: c for c in user_cats}
    cat_by_name = {c.name.lower().strip(): c for c in user_cats}

    # 4. Parse CSV
    reader = csv.reader(io.StringIO(csv_text))
    rows = [row for row in reader if row and any(cell.strip() for cell in row)]
    if not rows:
        return {"importedCount": 0, "imported_count": 0}

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

        clean_cat = cat_val.strip()
        matched_cat_id: str | None = None

        if clean_cat in cat_by_id:
            matched_cat_id = cat_by_id[clean_cat].id
        elif clean_cat.lower() in cat_by_name:
            matched_cat_id = cat_by_name[clean_cat.lower()].id
        else:
            normalized_name = clean_cat.replace("cat-", "").replace("-", " ").replace("_", " ").title() or "Other Expenses"
            if normalized_name.lower() in cat_by_name:
                matched_cat_id = cat_by_name[normalized_name.lower()].id
            else:
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

        tx = Transaction(
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
        db.add(tx)
        imported += 1

    await db.flush()
    return {"importedCount": imported, "imported_count": imported}
