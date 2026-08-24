"""
Finpluse v2 -- Base Agent (ReAct Pattern)

State machine for autonomous financial agents with reasoning traces.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class AgentState(str, Enum):
    IDLE = "IDLE"
    TRIGGERED = "TRIGGERED"
    REASONING = "REASONING"
    ACTION_PENDING = "ACTION_PENDING"
    CONFIRMED = "CONFIRMED"
    EXECUTED = "EXECUTED"
    VERIFYING = "VERIFYING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


@dataclass
class AgentContext:
    user_id: str
    session_id: str
    state: AgentState = AgentState.IDLE
    memory: dict[str, Any] = field(default_factory=dict)
    tools_used: list[str] = field(default_factory=list)
    pending_action: dict[str, Any] | None = None
    reasoning_trace: list[dict[str, Any]] = field(default_factory=list)


class BaseAgent:
    """Base class for all Finpluse autonomous agents."""

    name = "base_agent"
    description = "Abstract base agent"

    def __init__(self) -> None:
        self.tools: dict[str, Callable] = {}

    def register_tool(self, name: str, func: Callable) -> None:
        """Register a tool the agent can use."""
        self.tools[name] = func

    def _log_reasoning(self, ctx: AgentContext, step: str, thought: str) -> None:
        """Log a reasoning step."""
        ctx.reasoning_trace.append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "step": step,
            "thought": thought,
        })
        logger.debug(f"[{self.name}] {step}: {thought}")

    def execute_tool(self, ctx: AgentContext, tool_name: str, **kwargs: Any) -> Any:
        """Execute a registered tool and log it."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found")
        
        self._log_reasoning(ctx, "ACTION", f"Executing tool: {tool_name} with args {kwargs}")
        try:
            result = self.tools[tool_name](**kwargs)
            self._log_reasoning(ctx, "OBSERVATION", f"Tool {tool_name} returned: {result}")
            ctx.tools_used.append(tool_name)
            return result
        except Exception as e:
            self._log_reasoning(ctx, "ERROR", f"Tool {tool_name} failed: {e}")
            raise

    async def run(self, user_id: str, trigger_data: dict[str, Any]) -> AgentContext:
        """Main execution loop for the agent."""
        import uuid
        ctx = AgentContext(
            user_id=user_id,
            session_id=str(uuid.uuid4()),
            state=AgentState.TRIGGERED,
            memory=trigger_data
        )

        try:
            ctx.state = AgentState.REASONING
            self._log_reasoning(ctx, "START", f"Agent {self.name} triggered")
            
            await self._reason_and_act(ctx)
            
            if ctx.state == AgentState.REASONING:
                ctx.state = AgentState.COMPLETE
                self._log_reasoning(ctx, "FINISH", "Task complete")
                
        except Exception as e:
            ctx.state = AgentState.FAILED
            self._log_reasoning(ctx, "FAIL", f"Agent failed: {e}")
            logger.error(f"Agent {self.name} failed: {e}", exc_info=True)

        return ctx

    async def _reason_and_act(self, ctx: AgentContext) -> None:
        """Override this method with specific agent logic."""
        raise NotImplementedError
