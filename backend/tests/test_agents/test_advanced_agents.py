import pytest
from app.agents.subscription_watchdog import SubscriptionWatchdogAgent
from app.agents.bill_negotiation_agent import BillNegotiationAgent
from app.agents.base_agent import AgentState

@pytest.mark.asyncio
async def test_subscription_watchdog():
    agent = SubscriptionWatchdogAgent()
    ctx = await agent.run(user_id="test_user", trigger_data={})
    
    assert ctx.state == AgentState.ACTION_PENDING
    assert ctx.pending_action is not None
    assert ctx.pending_action["action"] == "NOTIFY_USER"
    
    findings = ctx.pending_action["payload"]
    assert len(findings) > 0
    types = [f["type"] for f in findings]
    assert "PRICE_HIKE" in types or "DUPLICATE_SERVICE" in types

@pytest.mark.asyncio
async def test_bill_negotiation_agent():
    agent = BillNegotiationAgent()
    ctx = await agent.run(user_id="test_user", trigger_data={})
    
    assert ctx.state == AgentState.ACTION_PENDING
    assert ctx.pending_action is not None
    assert ctx.pending_action["action"] == "PRESENT_NEGOTIATION_OPPORTUNITIES"
    
    opps = ctx.pending_action["payload"]
    assert len(opps) > 0
    # Comcast Xfinity is 110, avg is 60. That's > 1.15 * 60 (which is 69). So it should be flagged.
    assert opps[0]["merchant"] == "Comcast Xfinity"
