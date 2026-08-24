"""
Finpluse v2 -- Anomaly Alert System

Severity classification, smart grouping, and digest mode.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class AlertManager:
    """Manages anomaly alerts with severity, grouping, and digest support.

    Severity Levels:
        INFO:     Score 0.3-0.5, unusual but probably legitimate
        WARNING:  Score 0.5-0.7, likely anomaly
        CRITICAL: Score > 0.7, high confidence fraud
    """

    def __init__(self, grouping_window_minutes: int = 60, max_alerts_per_burst: int = 3) -> None:
        self.grouping_window_minutes = grouping_window_minutes
        self.max_alerts_per_burst = max_alerts_per_burst
        self._alerts: list[dict[str, Any]] = []
        self._grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._last_alert_time: dict[str, datetime] = {}

    def create_alert(self, user_id: str, transaction: dict[str, Any],
                     anomaly_result: dict[str, Any]) -> dict[str, Any] | None:
        """Create an alert from an anomaly detection result.

        Applies smart grouping to avoid alert fatigue.

        Args:
            user_id: User identifier.
            transaction: Transaction data.
            anomaly_result: Output from meta-classifier.

        Returns:
            Alert dict if not suppressed by grouping, None if grouped into existing alert.
        """
        probability = anomaly_result.get("probability", 0)
        if probability < 0.3:
            return None

        severity = anomaly_result.get("severity", "INFO")
        now = datetime.utcnow()

        # Smart grouping: check if similar alert was recently created
        merchant = transaction.get("merchant", "unknown")
        group_key = f"{user_id}:{merchant}:{severity}"

        last_time = self._last_alert_time.get(group_key)
        if last_time and (now - last_time) < timedelta(minutes=self.grouping_window_minutes):
            # Group into existing alert
            self._grouped[group_key].append(transaction)
            if len(self._grouped[group_key]) <= self.max_alerts_per_burst:
                return None  # Suppress, grouped
            else:
                # Too many in burst, escalate
                severity = "CRITICAL"

        alert = {
            "id": f"alert-{len(self._alerts)}-{int(now.timestamp())}",
            "user_id": user_id,
            "severity": severity,
            "probability": round(probability, 4),
            "transaction": {
                "amount": transaction.get("amount"),
                "merchant": merchant,
                "date": transaction.get("date"),
                "category_id": transaction.get("category_id"),
            },
            "fired_detectors": anomaly_result.get("fired_detectors", []),
            "explanation": anomaly_result.get("explanation", ""),
            "created_at": now.isoformat() + "Z",
            "acknowledged": False,
            "dismissed": False,
            "grouped_count": len(self._grouped.get(group_key, [])),
        }

        self._alerts.append(alert)
        self._last_alert_time[group_key] = now
        self._grouped[group_key] = [transaction]

        return alert

    def get_alerts(self, user_id: str, severity: str | None = None,
                   acknowledged: bool | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """Get alerts for a user with optional filtering."""
        filtered = [a for a in self._alerts if a["user_id"] == user_id]
        if severity:
            filtered = [a for a in filtered if a["severity"] == severity]
        if acknowledged is not None:
            filtered = [a for a in filtered if a["acknowledged"] == acknowledged]
        return sorted(filtered, key=lambda a: a["created_at"], reverse=True)[:limit]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Mark an alert as acknowledged."""
        for alert in self._alerts:
            if alert["id"] == alert_id:
                alert["acknowledged"] = True
                return True
        return False

    def dismiss_alert(self, alert_id: str) -> bool:
        """Dismiss an alert (user confirms it's legitimate)."""
        for alert in self._alerts:
            if alert["id"] == alert_id:
                alert["dismissed"] = True
                alert["acknowledged"] = True
                return True
        return False

    def get_daily_digest(self, user_id: str) -> dict[str, Any]:
        """Generate a daily summary of anomalies."""
        cutoff = datetime.utcnow() - timedelta(hours=24)
        recent = [a for a in self._alerts
                  if a["user_id"] == user_id and a["created_at"] > cutoff.isoformat()]

        return {
            "user_id": user_id,
            "period": "24h",
            "total_alerts": len(recent),
            "by_severity": {
                "CRITICAL": len([a for a in recent if a["severity"] == "CRITICAL"]),
                "WARNING": len([a for a in recent if a["severity"] == "WARNING"]),
                "INFO": len([a for a in recent if a["severity"] == "INFO"]),
            },
            "top_alerts": recent[:5],
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }


# Singleton
alert_manager = AlertManager()
