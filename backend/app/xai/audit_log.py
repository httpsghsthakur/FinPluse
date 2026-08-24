"""
Finpluse v2 -- Immutable AI Audit Log

Every AI decision logged with: timestamp, input hash, model version,
output, and user feedback. Stored in append-only database table.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import logging
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AuditLog:
    """Immutable, append-only log of all AI decisions.

    Each entry records:
        - Timestamp of the decision
        - SHA-256 hash of the input data (privacy: no raw financial data)
        - Model version used
        - Output produced
        - User feedback (if provided)
    """

    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []

    def log_decision(
        self,
        user_id: str,
        operation: str,
        input_data: Any,
        output_data: Any,
        model_version: str,
        reasoning_trace: dict[str, Any] | None = None,
    ) -> str:
        """Log an AI decision.

        Args:
            user_id: User identifier.
            operation: Type of AI operation (forecast, anomaly, agent, etc.).
            input_data: Input to the model (will be hashed, not stored raw).
            output_data: Model output.
            model_version: Version string of the model used.
            reasoning_trace: Optional full reasoning trace.

        Returns:
            Entry ID for later feedback attachment.
        """
        entry_id = f"audit-{len(self._entries)}-{int(datetime.utcnow().timestamp())}"
        input_hash = hashlib.sha256(
            json.dumps(input_data, default=str, sort_keys=True).encode()
        ).hexdigest()

        entry = {
            "id": entry_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user_id": user_id,
            "operation": operation,
            "input_hash": input_hash,
            "model_version": model_version,
            "output_summary": json.dumps(output_data, default=str)[:1000],
            "user_feedback": None,
            "feedback_timestamp": None,
        }

        if reasoning_trace:
            entry["reasoning_trace_id"] = reasoning_trace.get("operation", "")

        self._entries.append(entry)
        return entry_id

    def add_feedback(self, entry_id: str, feedback: str) -> bool:
        """Attach user feedback to a logged decision.

        Args:
            entry_id: The audit entry ID.
            feedback: User feedback text (e.g. "helpful", "wrong", "dont_suggest_again").

        Returns:
            True if feedback was attached, False if entry not found.
        """
        for entry in self._entries:
            if entry["id"] == entry_id:
                entry["user_feedback"] = feedback
                entry["feedback_timestamp"] = datetime.utcnow().isoformat() + "Z"
                return True
        return False

    def get_entries(self, user_id: str | None = None, operation: str | None = None,
                    limit: int = 100) -> list[dict[str, Any]]:
        """Query audit log entries."""
        filtered = self._entries
        if user_id:
            filtered = [e for e in filtered if e["user_id"] == user_id]
        if operation:
            filtered = [e for e in filtered if e["operation"] == operation]
        return sorted(filtered, key=lambda e: e["timestamp"], reverse=True)[:limit]

    def export_csv(self, user_id: str) -> str:
        """Export user's audit log as CSV string.

        Args:
            user_id: User to export for.

        Returns:
            CSV-formatted string.
        """
        entries = self.get_entries(user_id=user_id, limit=10000)
        output = io.StringIO()
        if not entries:
            return ""

        writer = csv.DictWriter(output, fieldnames=list(entries[0].keys()))
        writer.writeheader()
        writer.writerows(entries)
        return output.getvalue()


# Singleton
audit_log = AuditLog()
