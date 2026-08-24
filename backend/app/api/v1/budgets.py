"""Budgets endpoints — computes spent/predicted from live transaction data."""
from __future__ import annotations
from app.api.deps import get_current_user
from app.db.models.user import User

from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.transaction import Transaction
from app.db.models.category import Category
from app.schemas.budget import BudgetResponse, BudgetUpdate
from app.schemas.category import CategoryResponse


router = APIRouter()


@router.get("", response_model=list[BudgetResponse])
async def get_budgets(
    month: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_month = month or datetime.now().strftime("%Y-%m")

    # Get expense categories
    cat_result = await db.execute(
        select(Category).where(
            Category.user_id == current_user.id, Category.type == "expense"
        )
    )
    categories = cat_result.scalars().all()

    from calendar import monthrange
    year, mon = map(int, target_month.split("-"))
    start_date = date(year, mon, 1)
    _, last_day = monthrange(year, mon)
    end_date = date(year, mon, last_day)

    # Get spending for the month
    tx_result = await db.execute(
        select(Transaction.category_id, func.sum(Transaction.amount)).where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.amount < 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date,
            )
        ).group_by(Transaction.category_id)
    )
    spending_by_cat = {row[0]: abs(row[1]) for row in tx_result.all()}

    current_day = datetime.now().day
    days_in_month = 30

    budgets = []
    for cat in categories:
        spent = round(spending_by_cat.get(cat.id, 0), 2)
        pacing = (spent / current_day * days_in_month) if current_day > 0 else spent
        predicted = round(pacing, 2)

        budgets.append({
            "id": f"bgt-{cat.id}-{target_month}",
            "categoryId": cat.id,
            "monthlyLimit": cat.monthly_budget or 0,
            "spent": spent,
            "month": target_month,
            "predictedSpend": predicted,
        })

    return budgets


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_budget(
    category_id: str,
    data: BudgetUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a category's monthly budget limit."""
    result = await db.execute(
        select(Category).where(
            Category.id == category_id, Category.user_id == current_user.id
        )
    )
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    cat.monthly_budget = data.monthly_limit
    await db.flush()

    return {
        "id": cat.id,
        "name": cat.name,
        "icon": cat.icon,
        "color": cat.color,
        "type": cat.type,
        "monthlyBudget": cat.monthly_budget,
        "defaultMonthlyBudget": cat.default_monthly_budget,
        "isSystem": cat.is_system,
        "isCustom": cat.is_custom,
    }
