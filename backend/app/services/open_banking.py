"""
Finpluse v2 -- Open Banking Aggregation Service

Interface for Plaid, MX, or simulated connections.
Provides uniform API for transactions, balances, and webhooks.
"""
import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class OpenBankingService:
    """Abstracts underlying bank aggregators (Plaid, MX)."""

    def __init__(self, provider: str = "mock") -> None:
        self.provider = provider
        logger.info(f"Initialized OpenBankingService with provider: {provider}")

    def create_link_token(self, user_id: str) -> str:
        """Create token for frontend UI to connect institution."""
        return f"{self.provider}-link-{user_id}-{int(datetime.utcnow().timestamp())}"

    def exchange_public_token(self, public_token: str) -> str:
        """Exchange frontend token for permanent access token."""
        return f"access-{public_token}"

    def sync_transactions(self, access_token: str, start_date: str | None = None) -> list[dict[str, Any]]:
        """Fetch transactions from bank."""
        if self.provider == "mock":
            return self._generate_mock_transactions()
        raise NotImplementedError("Only mock provider is implemented for this demo")

    def _generate_mock_transactions(self) -> list[dict[str, Any]]:
        """Generate realistic mock transactions."""
        import random
        txs = []
        now = datetime.utcnow()
        merchants = [("Whole Foods", "cat-food"), ("Uber", "cat-transport"), 
                     ("Netflix", "cat-utilities"), ("Amazon", "cat-shopping")]
                     
        for i in range(20):
            merchant, cat = random.choice(merchants)
            amount = -round(random.uniform(10, 150), 2)
            date = (now - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d")
            
            txs.append({
                "transaction_id": f"tx_mock_{i}",
                "amount": amount,
                "merchant": merchant,
                "category_id": cat,
                "date": date,
                "pending": False
            })
            
        return txs
