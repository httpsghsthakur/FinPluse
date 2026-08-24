"""Categories endpoints."""
from __future__ import annotations
from app.api.deps import get_current_user
from app.db.models.user import User

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.category import Category
from app.schemas.category import CategoryResponse, CategoryCreate, CategoryUpdate


router = APIRouter()


def _cat_to_response(cat: Category) -> dict:
    return {
        "id": cat.id,
        "name": cat.name,
        "icon": cat.icon,
        "color": cat.color,
        "type": cat.type,
        "monthlyBudget": cat.monthly_budget,
        "defaultMonthlyBudget": cat.default_monthly_budget,
        "isSystem": cat.is_system,
        "isCustom": cat.is_custom,
    }


@router.get("", response_model=list[CategoryResponse])
async def get_categories(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Category).where(Category.user_id == current_user.id).order_by(Category.id)
    )
    return [_cat_to_response(c) for c in result.scalars().all()]


@router.post("", response_model=CategoryResponse, status_code=201)
async def add_category(data: CategoryCreate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),):
    cat = Category(
        id=f"cat-user-{int(datetime.utcnow().timestamp() * 1000)}",
        user_id=current_user.id,
        name=data.name,
        icon=data.icon,
        color=data.color,
        type=data.type,
        monthly_budget=data.monthly_budget,
        default_monthly_budget=data.default_monthly_budget,
        is_system=False,
        is_custom=True,
    )
    db.add(cat)
    await db.flush()
    return _cat_to_response(cat)


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str, data: CategoryUpdate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Category).where(Category.id == category_id, Category.user_id == current_user.id)
    )
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    for key, value in data.model_dump(exclude_unset=True, by_alias=False).items():
        setattr(cat, key, value)

    await db.flush()
    return _cat_to_response(cat)


@router.delete("/{category_id}", status_code=204)
async def delete_category(category_id: str, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),):
    result = await db.execute(
        select(Category).where(Category.id == category_id, Category.user_id == current_user.id)
    )
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    await db.delete(cat)
