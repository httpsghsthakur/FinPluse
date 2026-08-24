"""
Finpluse v2 -- Sustainability API
"""
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.db.models.user import User
from app.services.open_banking import OpenBankingService
from app.sustainability.calculator import aggregate_monthly_footprint
from app.sustainability.green_alternatives import suggest_alternatives

router = APIRouter()
banking_service = OpenBankingService()

@router.get("/footprint")
async def get_footprint(
    current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Get aggregated carbon footprint based on transactions."""
    # In a real app, we'd fetch actual transactions from DB for this user
    # For demo, we use mock from OpenBankingService
    txs = banking_service.sync_transactions("mock_token")
    
    totals = aggregate_monthly_footprint(txs)
    total_co2 = sum(totals.values())
    
    suggestions = suggest_alternatives(txs)
    
    return {
        "status": "success",
        "total_co2_kg": round(total_co2, 2),
        "by_category": {k: round(v, 2) for k, v in totals.items()},
        "suggestions": suggestions
    }
