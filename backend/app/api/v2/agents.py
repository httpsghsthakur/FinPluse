"""
Finpluse v2 -- Agent Management API
"""
from typing import Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.agents.auto_balance_agent import AutoBalanceAgent
from app.agents.subscription_watchdog import SubscriptionWatchdogAgent
from app.agents.bill_negotiation_agent import BillNegotiationAgent
from app.agents.scheduler import schedule_agent_job

router = APIRouter()

class ScheduleRequest(BaseModel):
    user_id: str
    trigger_type: str = "interval"
    minutes: int | None = None
    hours: int | None = None
    days: int | None = None

@router.post("/trigger/{agent_name}")
async def trigger_agent(agent_name: str, user_id: str) -> dict[str, Any]:
    """Trigger an autonomous agent."""
    agent_map = {
        "auto_balance": AutoBalanceAgent,
        "subscription_watchdog": SubscriptionWatchdogAgent,
        "bill_negotiation": BillNegotiationAgent
    }
    
    agent_cls = agent_map.get(agent_name)
    if not agent_cls:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    agent = agent_cls()
    ctx = await agent.run(user_id=user_id, trigger_data={})
    return {
        "session_id": ctx.session_id,
        "state": ctx.state.value,
        "pending_action": ctx.pending_action,
        "reasoning_trace": ctx.reasoning_trace
    }

@router.post("/schedule/{agent_name}")
async def schedule_agent(agent_name: str, req: ScheduleRequest, background_tasks: BackgroundTasks):
    """Schedule an agent to run repeatedly."""
    trigger_args = {}
    if req.minutes:
        trigger_args["minutes"] = req.minutes
    if req.hours:
        trigger_args["hours"] = req.hours
    if req.days:
        trigger_args["days"] = req.days
        
    background_tasks.add_task(
        schedule_agent_job,
        user_id=req.user_id,
        agent_name=agent_name,
        trigger_data={},
        trigger_type=req.trigger_type,
        **trigger_args
    )
    return {"status": "scheduled", "agent": agent_name, "user_id": req.user_id}
