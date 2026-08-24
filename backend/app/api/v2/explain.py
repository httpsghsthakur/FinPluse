"""
Finpluse v2 -- Explainable AI API

On-demand explanations for any AI output.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.xai.audit_log import audit_log
from app.xai.reasoning_trace import create_forecast_trace

router = APIRouter()


@router.get("/audit/{user_id}")
async def get_audit_log(user_id: str, operation: str | None = None, limit: int = 50) -> dict[str, Any]:
    """Get AI decision audit log for a user."""
    entries = audit_log.get_entries(user_id=user_id, operation=operation, limit=limit)
    return {"entries": entries, "total": len(entries)}


@router.get("/audit/{user_id}/export")
async def export_audit_csv(user_id: str) -> dict[str, str]:
    """Export audit log as CSV."""
    csv_data = audit_log.export_csv(user_id)
    return {"csv": csv_data}


@router.post("/audit/{entry_id}/feedback")
async def submit_feedback(entry_id: str, feedback: str) -> dict[str, bool]:
    """Submit user feedback on an AI decision."""
    success = audit_log.add_feedback(entry_id, feedback)
    return {"success": success}
