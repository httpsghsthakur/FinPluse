"""
Finpluse v2 -- Bill Negotiation Agent

Identifies negotiable bills, compares against market rates, and generates
personalized negotiation scripts for the user.
"""
import logging
from typing import Any

from .base_agent import BaseAgent, AgentContext, AgentState

logger = logging.getLogger(__name__)

class BillNegotiationAgent(BaseAgent):
    """
    Agent that analyzes recurring bills, checks market rates, and
    provides negotiation scripts if the user is overpaying.
    """
    name = "bill_negotiation"
    description = "Identifies overpaid bills and generates negotiation scripts"

    def __init__(self) -> None:
        super().__init__()
        # Register tools
        self.register_tool("fetch_recurring_bills", self._fetch_recurring_bills)
        self.register_tool("get_market_rates", self._get_market_rates)
        self.register_tool("generate_script", self._generate_script)

    def _fetch_recurring_bills(self, user_id: str) -> list[dict[str, Any]]:
        """Mock tool to fetch user's recurring bills."""
        return [
            {"merchant": "Comcast Xfinity", "amount": 110.00, "category": "Internet", "duration_months": 24},
            {"merchant": "AT&T", "amount": 85.00, "category": "Phone", "duration_months": 12},
            {"merchant": "State Farm", "amount": 150.00, "category": "Insurance", "duration_months": 36},
        ]

    def _get_market_rates(self, category: str) -> dict[str, Any]:
        """Mock tool to fetch current market rates for a category."""
        market_data = {
            "Internet": {"avg_rate": 60.00, "negotiable": True, "competitors": ["Verizon Fios", "Google Fiber"]},
            "Phone": {"avg_rate": 50.00, "negotiable": True, "competitors": ["T-Mobile", "Verizon"]},
            "Insurance": {"avg_rate": 120.00, "negotiable": True, "competitors": ["Geico", "Progressive"]},
        }
        return market_data.get(category, {"avg_rate": 0, "negotiable": False, "competitors": []})

    def _generate_script(self, merchant: str, current_rate: float, target_rate: float, competitors: list[str]) -> str:
        """Generates a negotiation script."""
        comps = ", ".join(competitors)
        return f"Hi, I've been a loyal customer of {merchant} for a while, but my bill is currently ${current_rate}. I noticed that competitors like {comps} are offering similar services for around ${target_rate}. Is there any retention promotion or discount you can apply to my account to match these rates?"

    async def _reason_and_act(self, ctx: AgentContext) -> None:
        self._log_reasoning(ctx, "THOUGHT", f"Checking for negotiable bills.")
        
        # 1. Fetch bills
        bills = self.execute_tool(ctx, "fetch_recurring_bills", user_id=ctx.user_id)
        
        opportunities = []
        
        # 2. Check each bill against market rates
        for bill in bills:
            market_info = self.execute_tool(ctx, "get_market_rates", category=bill["category"])
            
            if market_info["negotiable"] and bill["amount"] > market_info["avg_rate"] * 1.15:
                # 15% higher than average
                savings = bill["amount"] - market_info["avg_rate"]
                self._log_reasoning(ctx, "OBSERVATION", f"{bill['merchant']} bill is high. Paying ${bill['amount']}, average is ${market_info['avg_rate']}.")
                
                script = self.execute_tool(
                    ctx, "generate_script", 
                    merchant=bill["merchant"], 
                    current_rate=bill["amount"], 
                    target_rate=market_info["avg_rate"],
                    competitors=market_info["competitors"]
                )
                
                opportunities.append({
                    "merchant": bill["merchant"],
                    "current_amount": bill["amount"],
                    "target_amount": market_info["avg_rate"],
                    "potential_annual_savings": savings * 12,
                    "script": script
                })

        ctx.memory["negotiation_opportunities"] = opportunities
        if opportunities:
            self._log_reasoning(ctx, "THOUGHT", f"Found {len(opportunities)} negotiation opportunities.")
            ctx.pending_action = {
                "action": "PRESENT_NEGOTIATION_OPPORTUNITIES",
                "payload": opportunities
            }
            ctx.state = AgentState.ACTION_PENDING
        else:
            self._log_reasoning(ctx, "THOUGHT", "No overpaid bills found.")
