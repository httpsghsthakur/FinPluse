"""Simulator endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.account import Account
from app.db.models.goal import Goal
from app.schemas.simulator import ScenarioRequest, ScenarioResultResponse
from app.services.simulator_service import simulator_service


router = APIRouter()


@router.post("/run", response_model=ScenarioResultResponse)
async def run_simulation(
    scenario: ScenarioRequest,
    db: AsyncSession = Depends(get_db),
):
    # Get accounts
    acc_result = await db.execute(
        select(Account).where(Account.user_id == current_user.id)
    )
    accounts = [
        {"id": a.id, "type": a.type, "balance": a.balance}
        for a in acc_result.scalars().all()
    ]

    # Get goals
    goal_result = await db.execute(
        select(Goal).where(Goal.user_id == current_user.id)
    )
    goals = [
        {
            "id": g.id, "name": g.name,
            "target_amount": g.target_amount,
            "current_amount": g.current_amount,
            "monthly_contribution": g.monthly_contribution,
        }
        for g in goal_result.scalars().all()
    ]

    return simulator_service.run_simulation(scenario, accounts, goals)
