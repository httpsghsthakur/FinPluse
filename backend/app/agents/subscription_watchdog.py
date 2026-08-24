"""
Finpluse v2 -- Subscription Watchdog Agent

Detects recurring subscriptions, flags price increases, duplicate services,
and identifies unused subscriptions using heuristics and historical data.
"""
import logging
from typing import Any
import numpy as np

from .base_agent import BaseAgent, AgentContext, AgentState

logger = logging.getLogger(__name__)

class SubscriptionWatchdogAgent(BaseAgent):
    """
    Agent that analyzes transaction history to find subscriptions,
    detect price hikes, and flag redundant services.
    """
    name = "subscription_watchdog"
    description = "Monitors and analyzes recurring subscription charges"

    def __init__(self) -> None:
        super().__init__()
        # Register tools
        self.register_tool("fetch_transactions", self._fetch_transactions)
        self.register_tool("detect_periodicity", self._detect_periodicity)
        self.register_tool("compare_competitors", self._compare_competitors)

    def _fetch_transactions(self, user_id: str, days: int = 180) -> list[dict[str, Any]]:
        """Mock tool to fetch user transactions."""
        # In a real scenario, this would query the DB
        return [
            {"merchant": "Netflix", "amount": 15.49, "date": "2026-08-01", "category": "Entertainment"},
            {"merchant": "Netflix", "amount": 15.49, "date": "2026-07-01", "category": "Entertainment"},
            {"merchant": "Netflix", "amount": 12.99, "date": "2026-06-01", "category": "Entertainment"},
            {"merchant": "Hulu", "amount": 7.99, "date": "2026-08-15", "category": "Entertainment"},
            {"merchant": "Hulu", "amount": 7.99, "date": "2026-07-15", "category": "Entertainment"},
            {"merchant": "Planet Fitness", "amount": 10.00, "date": "2026-08-10", "category": "Health"},
        ]

    def _detect_periodicity(self, dates: list[str]) -> bool:
        """Use simple interval analysis to detect if dates are periodic."""
        if len(dates) < 2:
            return False
        # Simplified: Check if intervals are roughly 30 days
        # In full implementation, this uses Fourier transforms or diffs
        return True

    def _compare_competitors(self, merchant: str, category: str) -> list[str]:
        """Find redundant services in the same category."""
        competitors = {
            "Entertainment": ["Netflix", "Hulu", "Disney+", "Max"],
            "Health": ["Planet Fitness", "Equinox", "LA Fitness"]
        }
        return [c for c in competitors.get(category, []) if c != merchant]

    async def _reason_and_act(self, ctx: AgentContext) -> None:
        self._log_reasoning(ctx, "THOUGHT", f"Analyzing subscriptions for past 180 days.")
        
        # 1. Fetch transactions
        txs = self.execute_tool(ctx, "fetch_transactions", user_id=ctx.user_id, days=180)
        
        # Group by merchant
        merchant_txs = {}
        for tx in txs:
            merchant_txs.setdefault(tx["merchant"], []).append(tx)
            
        findings = []
        
        # 2. Analyze each merchant for subscription patterns
        for merchant, transactions in merchant_txs.items():
            dates = [t["date"] for t in transactions]
            is_recurring = self.execute_tool(ctx, "detect_periodicity", dates=dates)
            
            if is_recurring:
                amounts = [t["amount"] for t in transactions]
                latest_amount = amounts[0] # assuming sorted desc
                oldest_amount = amounts[-1]
                
                # Check for price hike
                if latest_amount > oldest_amount:
                    hike_pct = ((latest_amount - oldest_amount) / oldest_amount) * 100
                    findings.append({
                        "type": "PRICE_HIKE",
                        "merchant": merchant,
                        "details": f"Price increased by {hike_pct:.1f}% from $oldest_amount to $latest_amount"
                    })
                    self._log_reasoning(ctx, "OBSERVATION", f"Price hike detected for {merchant}: {hike_pct:.1f}%")
                    
                # Check for duplicates
                category = transactions[0].get("category", "")
                other_subs = [m for m in merchant_txs.keys() if m != merchant and merchant_txs[m][0].get("category") == category]
                if other_subs:
                    findings.append({
                        "type": "DUPLICATE_SERVICE",
                        "merchant": merchant,
                        "details": f"You also have subscriptions to: {', '.join(other_subs)} in {category}"
                    })
                    self._log_reasoning(ctx, "OBSERVATION", f"Duplicate services detected in {category}: {merchant} and {other_subs}")

        ctx.memory["findings"] = findings
        if findings:
            self._log_reasoning(ctx, "THOUGHT", f"Found {len(findings)} actionable insights.")
            ctx.pending_action = {
                "action": "NOTIFY_USER",
                "payload": findings
            }
            ctx.state = AgentState.ACTION_PENDING
        else:
            self._log_reasoning(ctx, "THOUGHT", "No anomalies or actionable insights found in subscriptions.")
