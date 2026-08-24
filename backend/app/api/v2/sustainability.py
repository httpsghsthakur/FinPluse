"""
Finpluse v2 -- Sustainability API
"""
from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel

from app.sustainability.carbon_estimator import CarbonEstimator

router = APIRouter()
estimator = CarbonEstimator()

class CarbonRequest(BaseModel):
    amount: float
    merchant: str
    category_id: str = ""

@router.post("/estimate")
async def estimate_transaction(req: CarbonRequest) -> dict[str, Any]:
    """Estimate CO2 for a single transaction."""
    return estimator.estimate_transaction(req.amount, req.merchant, req.category_id)

@router.post("/aggregate")
async def aggregate_carbon(transactions: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate aggregated monthly footprint."""
    return estimator.aggregate_monthly(transactions)
