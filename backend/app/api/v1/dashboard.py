"""Dashboard summary endpoint — aggregates all financial data."""
from __future__ import annotations

from datetime import datetime, timedelta, date
from calendar import monthrange

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.account import Account
from app.db.models.transaction import Transaction
from app.db.models.category import Category
from app.db.models.recurring import RecurringTransaction
from app.schemas.dashboard import DashboardSummaryResponse
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """Compute live dashboard summary from real DB data."""

    # Get accounts
    acc_result = await db.execute(
        select(Account).where(Account.user_id == current_user.id)
    )
    accounts = acc_result.scalars().all()
    account_map = {a.id: a.name for a in accounts}

    checking = sum(a.balance for a in accounts if a.type == "checking")
    savings = sum(a.balance for a in accounts if a.type == "savings")
    credit = sum(a.balance for a in accounts if a.type == "credit")

    liquid_cash = checking + savings
    total_debt = abs(credit)
    net_worth = liquid_cash - total_debt

    # Current month spending
    today = date.today()
    start_date = date(today.year, today.month, 1)
    _, last_day = monthrange(today.year, today.month)
    end_date = date(today.year, today.month, last_day)

    # Get all transactions for the current month
    tx_result = await db.execute(
        select(Transaction).where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.category_id != "cat-transfers",
                Transaction.date >= start_date,
                Transaction.date <= end_date,
            )
        )
    )
    month_txs = tx_result.scalars().all()
    
    # Calculate current month's income and expenses
    current_month_income = sum(tx.amount for tx in month_txs if tx.amount > 0)
    current_month_expenses = abs(sum(tx.amount for tx in month_txs if tx.amount < 0))
    total_monthly_spend = current_month_expenses
    
    # Dynamic Savings Rate
    if current_month_income > 0:
        savings_rate = max(0.0, round(((current_month_income - current_month_expenses) / current_month_income) * 100, 1))
    else:
        savings_rate = 0.0

    # Get categories for budget total
    cat_result = await db.execute(
        select(Category).where(Category.user_id == current_user.id)
    )
    categories = cat_result.scalars().all()
    total_budget = sum(c.monthly_budget or 0 for c in categories)

    # Category spend breakdown
    expense_cats = [c for c in categories if c.type == "expense"]
    cat_spending: dict[str, float] = {}
    for tx in month_txs:
        if tx.amount < 0:
            cat_spending[tx.category_id] = cat_spending.get(tx.category_id, 0) + abs(tx.amount)

    category_spend = []
    for cat in expense_cats:
        spent = round(cat_spending.get(cat.id, 0), 2)
        if spent > 0 or cat.monthly_budget:
            category_spend.append({
                "categoryId": cat.id,
                "categoryName": cat.name,
                "color": cat.color,
                "amount": spent,
                "percentage": round((spent / (total_monthly_spend or 1)) * 100) if total_monthly_spend else 0,
                "budget": cat.monthly_budget or 0,
            })
    category_spend.sort(key=lambda x: x["amount"], reverse=True)

    # Dynamic Monthly Burn (Rolling 30 days)
    rolling_30_start = today - timedelta(days=30)
    rolling_tx_result = await db.execute(
        select(func.sum(Transaction.amount)).where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.amount < 0,
                Transaction.category_id != "cat-transfers",
                Transaction.date >= rolling_30_start,
                Transaction.date <= today,
            )
        )
    )
    rolling_30_spend = abs(rolling_tx_result.scalar() or 0.0)
    monthly_burn = rolling_30_spend if rolling_30_spend > 0 else 4100
    cash_runway = round(liquid_cash / monthly_burn, 1) if monthly_burn else 0

    # Recent transactions
    recent_result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .order_by(Transaction.date.desc())
        .limit(8)
    )
    recent_txs = recent_result.scalars().all()
    recent_transactions = []
    for tx in recent_txs:
        tags = tx.tags.split(",") if tx.tags else None
        recent_transactions.append({
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
        })

    # Dynamic Upcoming Bills
    rec_result = await db.execute(
        select(RecurringTransaction)
        .where(
            and_(
                RecurringTransaction.user_id == current_user.id,
                RecurringTransaction.is_active == True,
                RecurringTransaction.expected_next_date >= today
            )
        )
        .order_by(RecurringTransaction.expected_next_date.asc())
        .limit(5)
    )
    recs = rec_result.scalars().all()
    upcoming_bills = []
    for r in recs:
        days_away = (r.expected_next_date - today).days
        upcoming_bills.append({
            "id": r.id,
            "merchant": r.merchant,
            "amount": abs(r.expected_amount),
            "dueDate": r.expected_next_date.isoformat(),
            "categoryId": r.category_id or "cat-utilities",
            "accountName": account_map.get(r.account_id, "Main Checking"),
            "daysAway": days_away
        })

    # Dynamic Cash Flow History (Last 6 Months)
    cash_flow_history = []
    for i in range(5, -1, -1):
        # Determine start and end of the target month
        target_month_date = today.replace(day=1) - timedelta(days=i * 28)
        target_month_date = target_month_date.replace(day=1)
        _, t_last = monthrange(target_month_date.year, target_month_date.month)
        t_start = target_month_date
        t_end = target_month_date.replace(day=t_last)
        
        hist_tx_res = await db.execute(
            select(Transaction.amount).where(
                and_(
                    Transaction.user_id == current_user.id,
                    Transaction.category_id != "cat-transfers",
                    Transaction.date >= t_start,
                    Transaction.date <= t_end
                )
            )
        )
        hist_amounts = hist_tx_res.scalars().all()
        inc = sum(a for a in hist_amounts if a > 0)
        exp = abs(sum(a for a in hist_amounts if a < 0))
        sav = inc - exp
        
        cash_flow_history.append({
            "month": t_start.strftime("%b"),
            "income": round(inc),
            "expenses": round(exp),
            "savings": round(sav)
        })

    # Dynamic Net Worth MoM %
    current_month_net = current_month_income - current_month_expenses
    last_month_net_worth = net_worth - current_month_net
    if last_month_net_worth > 0:
        net_worth_mom_pct = round(((net_worth - last_month_net_worth) / last_month_net_worth) * 100, 1)
    else:
        net_worth_mom_pct = 0.0

    return {
        "netWorth": net_worth,
        "netWorthMomPct": net_worth_mom_pct,
        "monthlySpending": total_monthly_spend,
        "monthlyBudgetTotal": total_budget,
        "cashRunwayMonths": cash_runway,
        "savingsRatePct": savings_rate,
        "totalLiquidCash": liquid_cash,
        "totalDebt": total_debt,
        "cashFlowHistory": cash_flow_history,
        "categorySpend": category_spend,
        "recentTransactions": recent_transactions,
        "upcomingBills": upcoming_bills,
        "lowBalanceAlert": {
            "hasLowBalance": liquid_cash < 2000,
            "threshold": 2000,
        },
    }
