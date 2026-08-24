"""
Finpluse v2 -- Stream Processors

Processing topology for real-time transaction enrichment, scoring, and alerting.
Uses the EventBus for local development; production uses Kafka Streams (Faust).

Topology:
    transactions.raw
      -> Parse & Validate
      -> Enrich (user profile, features)
      -> Branch:
          -> Anomaly Scoring
          -> Forecast Update Trigger
          -> Category Spending Update
      -> transactions.scored
      -> Alert Generation
"""
from __future__ import annotations

import logging
import time
from typing import Any

from backend.streaming.event_bus import Event, event_bus

logger = logging.getLogger(__name__)


class TransactionProcessor:
    """Processes raw transaction events through the enrichment pipeline.

    Steps:
        1. Parse and validate incoming transaction
        2. Enrich with user profile and computed features
        3. Score for anomalies
        4. Update running statistics
        5. Generate alerts if needed
    """

    def __init__(self) -> None:
        self._user_profiles: dict[str, dict[str, Any]] = {}
        self._running_stats: dict[str, dict[str, float]] = {}
        self._processing_times: list[float] = []

    async def process_raw_transaction(self, event: Event) -> None:
        """Process a raw transaction event.

        Args:
            event: Raw transaction event from transactions.raw topic.
        """
        start = time.monotonic()

        try:
            tx = event.value
            user_id = tx.get("user_id", event.key)

            # Step 1: Validate
            if not self._validate_transaction(tx):
                logger.warning(f"Invalid transaction from user {user_id}")
                return

            # Step 2: Enrich
            enriched = self._enrich_transaction(tx, user_id)
            await event_bus.publish("transactions.enriched", user_id, enriched)

            # Step 3: Anomaly scoring
            anomaly_score = self._score_anomaly(enriched, user_id)
            enriched["anomaly_score"] = anomaly_score

            # Step 4: Publish scored transaction
            await event_bus.publish("transactions.scored", user_id, enriched)

            # Step 5: Alert if needed
            if anomaly_score > 0.5:
                severity = "CRITICAL" if anomaly_score > 0.7 else "WARNING"
                await event_bus.publish("alerts.generated", user_id, {
                    "type": "anomaly",
                    "severity": severity,
                    "transaction": enriched,
                    "score": anomaly_score,
                    "timestamp": time.time(),
                })

            # Step 6: Update running stats
            self._update_running_stats(user_id, enriched)

            elapsed_ms = (time.monotonic() - start) * 1000
            self._processing_times.append(elapsed_ms)

            if elapsed_ms > 200:
                logger.warning(f"Transaction processing took {elapsed_ms:.1f}ms (target <200ms)")

        except Exception as e:
            logger.error(f"Transaction processing error: {e}")

    def _validate_transaction(self, tx: dict[str, Any]) -> bool:
        """Validate transaction has required fields."""
        required = {"amount", "date"}
        return all(k in tx for k in required)

    def _enrich_transaction(self, tx: dict[str, Any], user_id: str) -> dict[str, Any]:
        """Enrich transaction with computed features."""
        enriched = dict(tx)
        enriched["user_id"] = user_id
        enriched["processed_at"] = time.time()

        # Add running statistics as context
        stats = self._running_stats.get(user_id, {})
        enriched["user_avg_amount"] = stats.get("avg_amount", 0)
        enriched["user_tx_count"] = stats.get("tx_count", 0)
        enriched["amount_deviation"] = 0.0

        if stats.get("avg_amount", 0) > 0:
            enriched["amount_deviation"] = abs(tx.get("amount", 0)) / stats["avg_amount"]

        return enriched

    def _score_anomaly(self, tx: dict[str, Any], user_id: str) -> float:
        """Quick anomaly scoring based on deviation from user profile."""
        deviation = tx.get("amount_deviation", 0)
        if deviation > 3.0:
            return min(1.0, 0.5 + (deviation - 3.0) * 0.1)
        elif deviation > 2.0:
            return 0.3 + (deviation - 2.0) * 0.2
        return max(0.0, deviation * 0.1)

    def _update_running_stats(self, user_id: str, tx: dict[str, Any]) -> None:
        """Update running statistics for user."""
        if user_id not in self._running_stats:
            self._running_stats[user_id] = {"avg_amount": 0, "tx_count": 0, "total": 0}

        stats = self._running_stats[user_id]
        amount = abs(tx.get("amount", 0))
        stats["tx_count"] += 1
        stats["total"] += amount
        stats["avg_amount"] = stats["total"] / stats["tx_count"]

    def get_p99_latency_ms(self) -> float:
        """Get P99 processing latency in milliseconds."""
        if not self._processing_times:
            return 0.0
        import numpy as np
        return float(np.percentile(self._processing_times[-1000:], 99))


class WindowAggregator:
    """Windowed aggregation for real-time spending summaries.

    Supports:
        - Tumbling windows (1-minute spending totals)
        - Sliding windows (7-day rolling averages)
        - Session windows (user activity sessions)
    """

    def __init__(self) -> None:
        self._tumbling_windows: dict[str, dict[str, float]] = {}
        self._sliding_buffers: dict[str, list[tuple[float, float]]] = {}

    async def process_scored_transaction(self, event: Event) -> None:
        """Aggregate scored transactions into windows.

        Args:
            event: Scored transaction from transactions.scored topic.
        """
        tx = event.value
        user_id = tx.get("user_id", event.key)
        amount = abs(tx.get("amount", 0))
        timestamp = tx.get("processed_at", time.time())

        # Tumbling window (1-minute buckets)
        minute_key = f"{user_id}:{int(timestamp // 60)}"
        if minute_key not in self._tumbling_windows:
            self._tumbling_windows[minute_key] = {"total": 0, "count": 0}
        self._tumbling_windows[minute_key]["total"] += amount
        self._tumbling_windows[minute_key]["count"] += 1

        # Sliding window buffer (keep 7 days)
        if user_id not in self._sliding_buffers:
            self._sliding_buffers[user_id] = []
        self._sliding_buffers[user_id].append((timestamp, amount))

        # Trim to 7 days
        cutoff = timestamp - 7 * 86400
        self._sliding_buffers[user_id] = [
            (t, a) for t, a in self._sliding_buffers[user_id] if t > cutoff
        ]

    def get_rolling_average(self, user_id: str, window_days: int = 7) -> float:
        """Get rolling average spending for a user."""
        if user_id not in self._sliding_buffers:
            return 0.0
        cutoff = time.time() - window_days * 86400
        recent = [a for t, a in self._sliding_buffers[user_id] if t > cutoff]
        return sum(recent) / max(len(recent), 1)


# Initialize processors
transaction_processor = TransactionProcessor()
window_aggregator = WindowAggregator()
