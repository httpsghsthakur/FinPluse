"""
Finpluse v2 -- Anomaly Detection & Alert Management API
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ml.anomaly.alert_system import alert_manager

router = APIRouter()


class AnomalyScoreRequest(BaseModel):
    user_id: str
    amount: float
    merchant: str = ""
    category_id: str = ""
    date: str = ""


@router.get("/alerts/{user_id}")
async def get_user_alerts(
    user_id: str,
    severity: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Get anomaly alerts for a user."""
    alerts = alert_manager.get_alerts(user_id, severity=severity, limit=limit)
    return {"alerts": alerts, "total": len(alerts)}


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str) -> dict[str, bool]:
    """Acknowledge an alert."""
    success = alert_manager.acknowledge_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"acknowledged": True}


@router.post("/alerts/{alert_id}/dismiss")
async def dismiss_alert(alert_id: str) -> dict[str, bool]:
    """Dismiss an alert as legitimate."""
    success = alert_manager.dismiss_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"dismissed": True}


@router.get("/digest/{user_id}")
async def get_daily_digest(user_id: str) -> dict[str, Any]:
    """Get daily anomaly digest for a user."""
    return alert_manager.get_daily_digest(user_id)
