"""Goals endpoints."""
from __future__ import annotations
from app.api.deps import get_current_user
from app.db.models.user import User

from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.goal import Goal
from app.db.models.transaction import Transaction
from app.schemas.goal import GoalResponse, GoalCreate, GoalUpdate, GoalContribute


router = APIRouter()


def _goal_to_response(g: Goal) -> dict:
    return {
        "id": g.id,
        "name": g.name,
        "targetAmount": g.target_amount,
        "currentAmount": g.current_amount,
        "deadline": g.deadline.isoformat() if isinstance(g.deadline, date) else str(g.deadline),
        "category": g.category or "",
        "linkedAccountId": g.linked_account_id or "",
        "monthlyContribution": g.monthly_contribution,
        "color": g.color,
        "icon": g.icon,
        "isCompleted": g.is_completed,
        "boostSuggestion": g.boost_suggestion,
    }


@router.get("", response_model=list[GoalResponse])
async def get_goals(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Goal).where(Goal.user_id == current_user.id).order_by(Goal.id)
    )
    return [_goal_to_response(g) for g in result.scalars().all()]


@router.post("", response_model=GoalResponse, status_code=201)
async def add_goal(data: GoalCreate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),):
    goal = Goal(
        id=f"goal-{int(datetime.utcnow().timestamp() * 1000)}",
        user_id=current_user.id,
        name=data.name,
        target_amount=data.target_amount,
        current_amount=data.current_amount,
        deadline=date.fromisoformat(data.deadline),
        category=data.category,
        linked_account_id=data.linked_account_id,
        monthly_contribution=data.monthly_contribution,
        color=data.color,
        icon=data.icon,
        is_completed=False,
        boost_suggestion=data.boost_suggestion,
    )
    db.add(goal)
    await db.flush()
    return _goal_to_response(goal)


@router.patch("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: str, data: GoalUpdate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id)
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    for key, value in data.model_dump(exclude_unset=True, by_alias=False).items():
        if key == "deadline" and isinstance(value, str):
            setattr(goal, key, date.fromisoformat(value))
        else:
            setattr(goal, key, value)

    if goal.current_amount >= goal.target_amount:
        goal.is_completed = True

    await db.flush()
    return _goal_to_response(goal)


@router.delete("/{goal_id}", status_code=204)
async def delete_goal(goal_id: str, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),):
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id)
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    await db.delete(goal)


@router.post("/{goal_id}/contribute", response_model=GoalResponse)
async def contribute_to_goal(
    goal_id: str, data: GoalContribute, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id)
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    goal.current_amount += data.amount
    if goal.current_amount >= goal.target_amount:
        goal.is_completed = True

    # Create transfer transaction
    tx = Transaction(
        id=f"tx-goal-contrib-{int(datetime.utcnow().timestamp() * 1000)}",
        user_id=current_user.id,
        date=date.today(),
        merchant=f"Goal Deposit: {goal.name}",
        category_id="cat-transfers",
        account_id=goal.linked_account_id or "acc-checking",
        amount=-data.amount,
        status="settled",
        is_recurring=False,
        notes=f"Automated boost to {goal.name}",
    )
    db.add(tx)
    await db.flush()

    return _goal_to_response(goal)
