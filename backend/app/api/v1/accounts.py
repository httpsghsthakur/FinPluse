"""Accounts endpoints."""
from __future__ import annotations
from app.api.deps import get_current_user
from app.db.models.user import User

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.account import Account
from app.schemas.account import AccountResponse, AccountCreate


router = APIRouter()


def _account_to_response(acc: Account) -> dict:
    return {
        "id": acc.id,
        "name": acc.name,
        "type": acc.type,
        "balance": acc.balance,
        "currency": acc.currency,
        "institution": acc.institution,
        "mask": acc.mask,
        "color": acc.color,
        "lastSynced": acc.last_synced.isoformat() if acc.last_synced else "",
        "isActive": acc.is_active,
    }


@router.get("", response_model=list[AccountResponse])
async def get_accounts(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Account).where(Account.user_id == current_user.id).order_by(Account.id)
    )
    accounts = result.scalars().all()
    return [_account_to_response(a) for a in accounts]


@router.post("", response_model=AccountResponse, status_code=201)
async def connect_account(data: AccountCreate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),):
    acc = Account(
        id=f"acc-{int(datetime.utcnow().timestamp() * 1000)}",
        user_id=current_user.id,
        name=data.name,
        type=data.type,
        balance=data.balance,
        currency=data.currency,
        institution=data.institution,
        mask=data.mask,
        color=data.color,
        is_active=True,
    )
    db.add(acc)
    await db.flush()
    return _account_to_response(acc)


@router.post("/{account_id}/sync", response_model=AccountResponse)
async def sync_account(account_id: str, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),):
    result = await db.execute(
        select(Account).where(Account.id == account_id, Account.user_id == current_user.id)
    )
    acc = result.scalar_one_or_none()
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    acc.last_synced = datetime.utcnow()
    await db.flush()
    return _account_to_response(acc)


@router.delete("/{account_id}", status_code=204)
async def disconnect_account(account_id: str, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),):
    result = await db.execute(
        select(Account).where(Account.id == account_id, Account.user_id == current_user.id)
    )
    acc = result.scalar_one_or_none()
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    await db.delete(acc)
