"""
Finpluse v2 -- Agent Management API
"""
from typing import Any
from fastapi import APIRouter, HTTPException

from app.agents.auto_balance_agent import AutoBalanceAgent

router = APIRouter()


@router.post("/trigger/{agent_name}")
async def trigger_agent(agent_name: str, user_id: str) -> dict[str, Any]:
    """Trigger an autonomous agent."""
    if agent_name == "auto_balance":
        agent = AutoBalanceAgent()
        ctx = await agent.run(user_id=user_id, trigger_data={})
        return {
            "session_id": ctx.session_id,
            "state": ctx.state.value,
            "pending_action": ctx.pending_action,
            "reasoning_trace": ctx.reasoning_trace
        }
    else:
        raise HTTPException(status_code=404, detail="Agent not found")
