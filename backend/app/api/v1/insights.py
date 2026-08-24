"""Insights endpoints."""
from __future__ import annotations
from app.api.deps import get_current_user
from app.db.models.user import User

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.insight import Insight
from app.db.models.transaction import Transaction
from app.db.models.category import Category
from app.schemas.insight import InsightResponse, WeeklyDigestResponse


router = APIRouter()


def _insight_to_response(ins: Insight) -> dict:
    grounded = ins.grounded_data if isinstance(ins.grounded_data, list) else []
    return {
        "id": ins.id,
        "title": ins.title,
        "description": ins.description,
        "severity": ins.severity,
        "type": ins.type,
        "date": ins.date.isoformat() if ins.date else "",
        "isDismissed": ins.is_dismissed,
        "isLiked": ins.is_liked,
        "whyExplanation": ins.why_explanation or "",
        "groundedData": grounded,
        "actionLabel": ins.action_label,
        "actionPath": ins.action_path,
    }


@router.get("", response_model=list[InsightResponse])
async def get_insights(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Insight).where(Insight.user_id == current_user.id).order_by(Insight.date.desc())
    )
    return [_insight_to_response(i) for i in result.scalars().all()]


@router.post("/{insight_id}/dismiss", status_code=204)
async def dismiss_insight(insight_id: str, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),):
    result = await db.execute(
        select(Insight).where(Insight.id == insight_id, Insight.user_id == current_user.id)
    )
    ins = result.scalar_one_or_none()
    if not ins:
        raise HTTPException(status_code=404, detail="Insight not found")
    ins.is_dismissed = True
    await db.flush()


@router.post("/{insight_id}/like", status_code=204)
async def like_insight(insight_id: str, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),):
    result = await db.execute(
        select(Insight).where(Insight.id == insight_id, Insight.user_id == current_user.id)
    )
    ins = result.scalar_one_or_none()
    if not ins:
        raise HTTPException(status_code=404, detail="Insight not found")
    ins.is_liked = not (ins.is_liked or False)
    await db.flush()


@router.get("/digest/weekly", response_model=WeeklyDigestResponse)
async def get_weekly_digest(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Weekly digest dynamically computed from recent transactions."""
    from datetime import datetime, timedelta, date
    now = datetime.now()
    today = now.date()
    week_start = today - timedelta(days=7)
    prev_week_start = week_start - timedelta(days=7)
    
    # Current week txs
    tx_res = await db.execute(
        select(Transaction).where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.date >= week_start,
                Transaction.date <= today
            )
        )
    )
    current_week_txs = tx_res.scalars().all()
    
    # Previous week txs
    prev_tx_res = await db.execute(
        select(Transaction).where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.date >= prev_week_start,
                Transaction.date < week_start
            )
        )
    )
    prev_week_txs = prev_tx_res.scalars().all()
    
    # Calculate metrics
    cw_income = sum(t.amount for t in current_week_txs if t.amount > 0)
    cw_expense = abs(sum(t.amount for t in current_week_txs if t.amount < 0))
    pw_expense = abs(sum(t.amount for t in prev_week_txs if t.amount < 0))
    
    # Category mapping
    cat_res = await db.execute(select(Category).where(Category.user_id == current_user.id))
    categories = {c.id: c.name for c in cat_res.scalars().all()}
    
    # Top Category
    cat_spend = {}
    anomalies = []
    for tx in current_week_txs:
        if tx.amount < 0 and tx.category_id != "cat-transfers":
            cat_spend[tx.category_id] = cat_spend.get(tx.category_id, 0) + abs(tx.amount)
        if getattr(tx, "is_anomaly", False):
            anomalies.append(tx)
            
    top_cat_id = max(cat_spend, key=cat_spend.get) if cat_spend else None
    top_cat_name = categories.get(top_cat_id, "General") if top_cat_id else "None"
    top_cat_amount = round(cat_spend.get(top_cat_id, 0), 2)
    
    # Vs Last Week
    if pw_expense > 0:
        vs_last_week = round(((cw_expense - pw_expense) / pw_expense) * 100, 1)
    else:
        vs_last_week = 0.0
        
    summary_title = "Solid week!"
    if vs_last_week > 10:
        summary_title = f"Spending is up {vs_last_week}% vs last week"
    elif vs_last_week < -10:
        summary_title = f"Great job! Spending is down {abs(vs_last_week)}% vs last week"
    elif top_cat_id:
        summary_title = f"Watch your {top_cat_name} spending"
        
    bullets = []
    if vs_last_week != 0:
        bullets.append(f"Total spending was {abs(vs_last_week)}% {'higher' if vs_last_week > 0 else 'lower'} than last week.")
        
    if top_cat_id:
        bullets.append(f"Your highest spending category was {top_cat_name} at ₹{top_cat_amount:,.2f}.")
        
    for a in anomalies:
        bullets.append(f"Unusual transaction flagged: {a.merchant} (₹{abs(a.amount):,.2f}).")
        
    if not bullets:
        bullets.append("Routine week, no major spending anomalies detected.")

    return {
        "weekRange": f"{week_start.strftime('%b %d')} – {now.strftime('%b %d, %Y')}",
        "summaryTitle": summary_title,
        "totalIncome": round(cw_income, 2),
        "totalExpenses": round(cw_expense, 2),
        "netSavings": round(cw_income - cw_expense, 2),
        "topCategoryName": top_cat_name,
        "topCategorySpend": top_cat_amount,
        "vsLastWeekPct": vs_last_week,
        "bullets": bullets,
        "actionableTip": "Review your highest spending category to see if you can cut back next week.",
        "anomaliesDetectedCount": len(anomalies),
    }
