"""
Finpluse v2 -- Auto-Balance Agent

Optimizes cash allocation between checking and high-yield savings.
Maintains 3-month emergency fund, sweeps excess.
"""
from __future__ import annotations

from typing import Any

from app.agents.base_agent import BaseAgent, AgentContext, AgentState


class AutoBalanceAgent(BaseAgent):
    name = "auto_balance"
    description = "Optimizes cash allocation between checking and savings"

    def __init__(self) -> None:
        super().__init__()
        # In a real app, these would call the actual database/APIs
        self.register_tool("get_account_balances", self._mock_get_balances)
        self.register_tool("get_monthly_burn", self._mock_get_burn)
        self.register_tool("propose_transfer", self._mock_propose_transfer)

    def _mock_get_balances(self, user_id: str) -> dict[str, float]:
        return {"checking": 15000.0, "savings": 5000.0}

    def _mock_get_burn(self, user_id: str) -> float:
        return 4000.0

    def _mock_propose_transfer(self, from_acc: str, to_acc: str, amount: float) -> dict[str, Any]:
        return {"transfer_id": "tx_999", "status": "pending_approval", "amount": amount}

    async def _reason_and_act(self, ctx: AgentContext) -> None:
        self._log_reasoning(ctx, "THOUGHT", "I need to check current balances and monthly burn rate.")
        
        balances = self.execute_tool(ctx, "get_account_balances", user_id=ctx.user_id)
        burn_rate = self.execute_tool(ctx, "get_monthly_burn", user_id=ctx.user_id)
        
        checking = balances.get("checking", 0)
        savings = balances.get("savings", 0)
        total_cash = checking + savings
        
        target_emergency_fund = burn_rate * 3  # 3 months runway
        
        self._log_reasoning(ctx, "THOUGHT", 
            f"Total cash is ${total_cash}. Target emergency fund (3x burn) is ${target_emergency_fund}.")
        
        if total_cash < target_emergency_fund:
            self._log_reasoning(ctx, "THOUGHT", "User does not have enough for 3-month emergency fund. No optimization possible.")
            return

        # Keep 1.5 months in checking, rest in savings
        target_checking = burn_rate * 1.5
        excess_checking = checking - target_checking

        if excess_checking > 500:
            self._log_reasoning(ctx, "THOUGHT", f"Checking has ${excess_checking} excess. Proposing transfer to savings.")
            transfer = self.execute_tool(ctx, "propose_transfer", 
                                         from_acc="checking", to_acc="savings", amount=excess_checking)
            ctx.pending_action = {
                "type": "transfer",
                "details": transfer,
                "reasoning": f"Sweeping ${excess_checking} excess cash to high-yield savings to maximize interest while maintaining 1.5 months runway in checking."
            }
            ctx.state = AgentState.ACTION_PENDING
        else:
            self._log_reasoning(ctx, "THOUGHT", "Allocation is near optimal. No action needed.")
