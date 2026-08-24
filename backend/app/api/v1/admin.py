"""Admin endpoints — reset data, export."""
from __future__ import annotations

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


async def seed_database(db: AsyncSession) -> None:
    """Seed the database with demo data."""
    # Check if demo user exists
    result = await db.execute(select(User).where(User.id == current_user.id))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        return  # Already seeded

    # Create user
    user_data = generate_user(current_user.id)
    user = User(
        id=user_data["id"],
        email=user_data["email"],
        name=user_data["name"],
        avatar_url=user_data["avatar_url"],
        currency=user_data["currency"],
        theme=user_data["theme"],
        first_day_of_month=user_data["first_day_of_month"],
        notifications_enabled=user_data["notifications_enabled"],
        chat_personality=user_data["chat_personality"],
        share_data_for_analytics=user_data["share_data_for_analytics"],
        is_2fa_enabled=user_data["is_2fa_enabled"],
        pin_code=user_data["pin_code"],
        consent_personalization=user_data["consent_personalization"],
        consent_global_training=user_data["consent_global_training"],
    )
    db.add(user)
    await db.flush()

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
            deadline=date.fromisoformat(goal_data["deadline"]),
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
            date=date.fromisoformat(tx_data["date"]),
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
            expected_next_date=datetime.fromisoformat(rec_data["expected_next_date"]).date(),
            confidence=rec_data["confidence"],
            last_seen_date=datetime.fromisoformat(rec_data["last_seen_date"]).date(),
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
            date=date.fromisoformat(ins_data["date"]),
            is_dismissed=ins_data["is_dismissed"],
            why_explanation=ins_data["why_explanation"],
            grounded_data=ins_data["grounded_data"],
            action_label=ins_data.get("action_label"),
            action_path=ins_data.get("action_path"),
        )
        db.add(ins)
    await db.flush()


@router.post("/reset", status_code=204)
async def reset_all_data(db: AsyncSession = Depends(get_db)):
    """Reset all demo data to initial state."""
    # Delete in dependency order
    await db.execute(delete(Transaction).where(Transaction.user_id == current_user.id))
    await db.execute(delete(RecurringTransaction).where(RecurringTransaction.user_id == current_user.id))
    await db.execute(delete(Insight).where(Insight.user_id == current_user.id))
    await db.execute(delete(Goal).where(Goal.user_id == current_user.id))
    await db.execute(delete(Account).where(Account.user_id == current_user.id))
    await db.execute(delete(Category).where(Category.user_id == current_user.id))
    await db.execute(delete(User).where(User.id == current_user.id))
    await db.flush()

    # Re-seed
    await seed_database(db)


@router.get("/export")
async def export_all_data(db: AsyncSession = Depends(get_db)):
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
        "categories": [{"id": c.id, "name": c.name, "icon": c.icon, "color": c.color, "type": c.type, "monthlyBudget": c.monthly_budget, "isSystem": c.is_system, "isCustom": c.is_custom} for c in cats],
        "goals": [{"id": g.id, "name": g.name, "targetAmount": g.target_amount, "currentAmount": g.current_amount, "deadline": g.deadline.isoformat() if isinstance(g.deadline, date) else str(g.deadline), "category": g.category, "linkedAccountId": g.linked_account_id, "monthlyContribution": g.monthly_contribution, "color": g.color, "icon": g.icon, "isCompleted": g.is_completed, "boostSuggestion": g.boost_suggestion} for g in goals],
        "transactions": [{"id": t.id, "date": t.date.isoformat() if isinstance(t.date, date) else str(t.date), "merchant": t.merchant, "categoryId": t.category_id, "accountId": t.account_id, "amount": t.amount, "status": t.status, "isRecurring": t.is_recurring, "isAnomaly": t.is_anomaly, "anomalyReason": t.anomaly_reason, "notes": t.notes} for t in txs],
        "recurring": [{"id": r.id, "merchant": r.merchant, "categoryId": r.category_id, "accountId": r.account_id, "isRecurring": r.is_recurring, "frequency": r.frequency, "expectedAmount": r.expected_amount, "expectedNextDate": r.expected_next_date.isoformat() if r.expected_next_date else None, "confidence": r.confidence, "isActive": r.is_active} for r in recs],
        "insights": [{"id": i.id, "title": i.title, "description": i.description, "severity": i.severity, "type": i.type, "date": i.date.isoformat() if i.date else "", "isDismissed": i.is_dismissed, "whyExplanation": i.why_explanation, "groundedData": i.grounded_data or [], "actionLabel": i.action_label, "actionPath": i.action_path} for i in insights],
    }

@router.post("/replace_transactions_from_csv", status_code=200)
async def replace_transactions_from_csv(data: dict, db: AsyncSession = Depends(get_db)):
    """Wipes all transactions and loads them from CSV text."""
    # Wipe transactions
    await db.execute(delete(Transaction).where(Transaction.user_id == current_user.id))
    
    csv_text = data.get("csvText", "")
    lines = csv_text.strip().split("\n")
    imported = 0

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
            tx = Transaction(
                id=f"tx-import-{int(datetime.utcnow().timestamp() * 1000)}-{i}",
                user_id=current_user.id,
                date=date.fromisoformat(date_str) if date_str else date.today(),
                merchant=merchant_str or "Imported Merchant",
                amount=amount,
                category_id=cat_str,
                account_id="acc-checking",
                status="settled",
                is_recurring=False,
            )
            db.add(tx)
            imported += 1

    await db.flush()
    return {"importedCount": imported}
