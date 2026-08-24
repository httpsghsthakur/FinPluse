"""
Finpluse v2 -- Reasoning Trace Generator

Creates structured, human-readable reasoning traces for every AI output.
Captures input data, model selection, intermediate calculations, and final results.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any


class ReasoningTrace:
    """Structured reasoning trace for AI transparency.

    Captures the full decision pipeline in a collapsible tree format
    suitable for frontend rendering.
    """

    def __init__(self, operation: str, user_id: str) -> None:
        self.operation = operation
        self.user_id = user_id
        self.steps: list[dict[str, Any]] = []
        self.started_at = datetime.utcnow().isoformat() + "Z"
        self._input_hash: str = ""

    def add_step(self, title: str, description: str,
                 data: dict[str, Any] | None = None,
                 substeps: list[dict[str, Any]] | None = None) -> "ReasoningTrace":
        """Add a reasoning step."""
        step = {
            "step_number": len(self.steps) + 1,
            "title": title,
            "description": description,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        if data:
            step["data"] = data
        if substeps:
            step["substeps"] = substeps
        self.steps.append(step)
        return self

    def set_input_hash(self, input_data: Any) -> "ReasoningTrace":
        """Hash the input data for audit purposes (no raw financial data in logs)."""
        serialized = json.dumps(input_data, default=str, sort_keys=True)
        self._input_hash = hashlib.sha256(serialized.encode()).hexdigest()[:16]
        return self

    def finalize(self, result: Any, model_version: str = "1.0") -> dict[str, Any]:
        """Finalize the trace with the final result.

        Returns:
            Complete trace document suitable for audit logging.
        """
        return {
            "operation": self.operation,
            "user_id": self.user_id,
            "input_hash": self._input_hash,
            "model_version": model_version,
            "started_at": self.started_at,
            "completed_at": datetime.utcnow().isoformat() + "Z",
            "steps": self.steps,
            "n_steps": len(self.steps),
            "result_summary": str(result)[:500] if result else None,
        }


def create_forecast_trace(user_id: str, n_transactions: int, n_features: int,
                          model_name: str, mape: float, point_estimate: float,
                          ci_lower: float, ci_upper: float) -> dict[str, Any]:
    """Create a standard forecast reasoning trace."""
    trace = ReasoningTrace("forecast", user_id)
    trace.add_step(
        "Input Data Collection",
        f"Retrieved {n_transactions} transactions from user history",
        data={"n_transactions": n_transactions},
    )
    trace.add_step(
        "Feature Engineering",
        f"Generated {n_features} features (lag, calendar, cyclical, velocity)",
        data={"n_features": n_features},
    )
    trace.add_step(
        "Model Selection",
        f"{model_name} selected based on lowest MAPE ({mape:.1%})",
        data={"model": model_name, "mape": mape},
    )
    trace.add_step(
        "Forecast Generation",
        f"Point estimate: ${point_estimate:,.2f}",
        data={"point_estimate": point_estimate},
    )
    trace.add_step(
        "Uncertainty Quantification",
        f"95% CI: ${ci_lower:,.2f} - ${ci_upper:,.2f}",
        data={"ci_lower": ci_lower, "ci_upper": ci_upper},
    )
    return trace.finalize(f"${point_estimate:,.2f} ({ci_lower:,.2f} - {ci_upper:,.2f})")
