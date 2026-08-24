"""
Finpluse v2 -- Open Banking API
"""
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.open_banking import OpenBankingService

router = APIRouter()
banking = OpenBankingService(provider="mock")

class LinkRequest(BaseModel):
    user_id: str

class ExchangeRequest(BaseModel):
    public_token: str


@router.post("/link/token")
async def create_link_token(req: LinkRequest) -> dict[str, str]:
    """Create token for Plaid Link UI."""
    return {"link_token": banking.create_link_token(req.user_id)}


@router.post("/link/exchange")
async def exchange_token(req: ExchangeRequest) -> dict[str, str]:
    """Exchange public token for access token."""
    access_token = banking.exchange_public_token(req.public_token)
    return {"access_token": access_token}


@router.post("/sync/{access_token}")
async def sync_transactions(access_token: str) -> dict[str, Any]:
    """Sync transactions from institution."""
    txs = banking.sync_transactions(access_token)
    return {"synced_count": len(txs), "transactions": txs}
