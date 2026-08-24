"""Tests for base agent."""
import pytest
from app.agents.base_agent import BaseAgent, AgentState

class DummyAgent(BaseAgent):
    name = "dummy"
    async def _reason_and_act(self, ctx):
        self.execute_tool(ctx, "echo", msg="hello")
        ctx.state = AgentState.ACTION_PENDING

@pytest.mark.asyncio
async def test_agent_run():
    agent = DummyAgent()
    agent.register_tool("echo", lambda msg: msg)
    ctx = await agent.run("user-1", {})
    assert ctx.state == AgentState.ACTION_PENDING
    assert "echo" in ctx.tools_used
    assert len(ctx.reasoning_trace) > 0
