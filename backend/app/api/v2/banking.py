"""
Finpluse v2 -- Open Banking API
"""
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.db.models.user import User
from app.services.open_banking import OpenBankingService

router = APIRouter()
banking_service = OpenBankingService()

class PublicTokenRequest(BaseModel):
    public_token: str

@router.post("/link/token")
async def create_link_token(
    current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Create token for frontend UI."""
    token = banking_service.create_link_token(str(current_user.id))
    return {"link_token": token}

@router.post("/link/exchange")
async def exchange_token(
    request: PublicTokenRequest,
    current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Exchange public token for access token."""
    access_token = banking_service.exchange_public_token(request.public_token)
    return {"status": "success", "access_token": access_token}

@router.get("/transactions/sync")
async def sync_transactions(
    current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Sync transactions from bank."""
    # Using mock token for demo
    txs = banking_service.sync_transactions("mock_token")
    return {"status": "success", "transactions": txs}
