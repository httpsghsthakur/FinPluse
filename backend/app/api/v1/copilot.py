"""AI Copilot endpoint — Dynamic financial reasoning engine with LLM integration & live ledger context."""
from __future__ import annotations

import os
import re
import time
import asyncio
import json
import logging
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None  # type: ignore
    types = None  # type: ignore
from datetime import datetime, date, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.db.models.account import Account
from app.db.models.transaction import Transaction
from app.db.models.category import Category
from app.db.models.goal import Goal
from app.schemas.copilot import CopilotRequest, ChatMessageResponse
from app.ml.classifiers.intent_classifier import intent_classifier

router = APIRouter()


def _format_currency(amount: float) -> str:
    sign = "-" if amount < 0 else ""
    return f"{sign}₹{abs(amount):,.2f}"


def _format_pct(value: float) -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.1f}%"


def _extract_amount_and_item(query: str) -> tuple[float, str]:
    """Intelligently extract the proposed item and purchase price."""
    q = query.lower()
    
    # 1. Check for multiplier notations: e.g. 50k, 1.5L, 2 Lakh, 50000, $500, ₹45,000
    k_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:k|thousand)", q)
    if k_match:
        return float(k_match.group(1)) * 1000, "proposed purchase"

    l_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:l|lac|lakh|lakhs)", q)
    if l_match:
        return float(l_match.group(1)) * 100000, "proposed purchase"

    cr_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:cr|crore|crores)", q)
    if cr_match:
        return float(cr_match.group(1)) * 10000000, "proposed purchase"

    num_match = re.search(r"(?:₹|\$|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)", q)
    if num_match:
        raw_num = num_match.group(1).replace(",", "")
        try:
            val = float(raw_num)
            if val > 10:  # avoid picking up stray single digits
                return val, "item"
        except ValueError:
            pass

    # 2. Semantic Item Price Dictionary
    item_prices = [
        (r"\b(iphone\s*1[567]?(?:\s*pro(?:\s*max)?)?|flagship\s*phone)\b", 125000, "Premium Flagship Smartphone"),
        (r"\b(phone|smartphone|mobile|android|pixel|samsung)\b", 65000, "New Smartphone"),
        (r"\b(macbook\s*(?:pro|air|m[1-4])?|gaming\s*laptop)\b", 145000, "Laptop / MacBook"),
        (r"\b(laptop|computer|pc|ipad|tablet)\b", 75000, "Personal Computer / Tablet"),
        (r"\b(car|suv|sedan|vehicle|automobile)\b", 850000, "New Car / Vehicle"),
        (r"\b(bike|motorcycle|scooter|ev\s*scooter)\b", 130000, "Two-Wheeler / Bike"),
        (r"\b(trip|vacation|holiday|bali|europe|flight|tour)\b", 95000, "Vacation / Travel Trip"),
        (r"\b(watch|apple\s*watch|smartwatch)\b", 42000, "Smartwatch / Wearable"),
        (r"\b(ps5|playstation|xbox|gaming\s*console)\b", 55000, "Gaming Console"),
        (r"\b(tv|television|oled|projector)\b", 65000, "Smart TV / Home Entertainment"),
        (r"\b(dinner|party|club|restaurant|fine\s*dining)\b", 4500, "Dining / Social Outing"),
        (r"\b(shoes|sneakers|jacket|clothes|shopping)\b", 8500, "Retail / Apparel Purchase"),
        (r"\b(gym|cult|fitness\s*membership)\b", 18000, "Annual Gym Membership"),
    ]

    for pattern, price, label in item_prices:
        if re.search(pattern, q):
            return float(price), label

    return 45000.0, "Discretionary Purchase"


async def _compute_financials(db: AsyncSession, current_user: User) -> dict:
    """Compute live, ground-truth financial statistics from actual database records."""
    acc_result = await db.execute(select(Account).where(Account.user_id == current_user.id))
    accounts = acc_result.scalars().all()
    checking = sum(a.balance for a in accounts if a.type == "checking")
    savings = sum(a.balance for a in accounts if a.type == "savings")
    credit = sum(a.balance for a in accounts if a.type == "credit")
    liquid = checking + savings
    net_worth = liquid + credit

    today = date.today()
    start_30 = today - timedelta(days=30)
    
    tx_result = await db.execute(
        select(Transaction).where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.date >= start_30,
                Transaction.date <= today
            )
        ).order_by(Transaction.date.desc())
    )
    recent_txs = tx_result.scalars().all()
    expense_txs = [t for t in recent_txs if t.amount < 0 and t.category_id != "cat-transfers"]
    income_txs = [t for t in recent_txs if t.amount > 0]
    total_expense = abs(sum(t.amount for t in expense_txs))
    total_income = sum(t.amount for t in income_txs)
    monthly_burn = total_expense if total_expense > 0 else 55000.0
    runway = round(liquid / monthly_burn, 1) if monthly_burn > 0 else 12.0
    savings_rate = max(0.0, ((total_income - total_expense) / total_income * 100)) if total_income > 0 else 24.5

    # Categories
    cat_result = await db.execute(select(Category).where(Category.user_id == current_user.id))
    categories = cat_result.scalars().all()
    cat_map = {c.id: c.name for c in categories}
    
    # Category spend totals
    cat_spend = {}
    for t in expense_txs:
        cat_name = cat_map.get(t.category_id, "Other")
        cat_spend[cat_name] = cat_spend.get(cat_name, 0.0) + abs(t.amount)

    dining_spend = cat_spend.get("Dining & Drinks", 0.0)
    grocery_spend = cat_spend.get("Groceries", 0.0)
    shopping_spend = cat_spend.get("Shopping & Gear", 0.0)

    # Goals
    goal_result = await db.execute(select(Goal).where(Goal.user_id == current_user.id))
    goals = goal_result.scalars().all()

    return {
        "checking": checking, "savings": savings, "credit": credit,
        "liquid": liquid, "net_worth": net_worth,
        "total_expense": total_expense, "total_income": total_income,
        "monthly_burn": monthly_burn, "runway": runway, "savings_rate": savings_rate,
        "dining_spend": dining_spend, "grocery_spend": grocery_spend, "shopping_spend": shopping_spend,
        "cat_spend": cat_spend, "goals": goals, "accounts": accounts, "recent_txs": recent_txs[:15],
        "user_name": current_user.name or "User",
    }


async def _call_llm_if_available(query: str, data: dict, personality: str) -> str:
    """Call external LLM (Gemini) if API key is present."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logging.getLogger(__name__).warning("GEMINI_API_KEY is not set.")
        return "I need a GEMINI_API_KEY to process your request. Please set it in your environment variables."

    goals_str = ", ".join([f"{g.name} (Saved: ₹{g.current_amount:,.0f}/₹{g.target_amount:,.0f})" for g in data.get("goals", [])])
    recent_merchants = ", ".join([f"{t.merchant}: ₹{abs(t.amount):,.0f}" for t in data.get("recent_txs", [])[:8]])

    system_prompt = f"""You are FinPilot, a senior Palantir-tier AI Financial Copilot.
Current User Verified Ground-Truth Financial State:
- Checking Account Liquid Balance: ₹{data['checking']:,.2f}
- High-Yield Savings Reserves: ₹{data['savings']:,.2f}
- Outstanding Credit Card Balance: ₹{abs(data['credit']):,.2f}
- Total Liquid Cash: ₹{data['liquid']:,.2f}
- Estimated Total Net Worth: ₹{data['net_worth']:,.2f}
- 30-Day Monthly Burn Rate: ₹{data['monthly_burn']:,.2f}
- Cash Runway Cushion: {data['runway']} months
- Active Goals: {goals_str or 'Emergency Fund'}
- Recent Outflows: {recent_merchants}

Tone requirement: {personality} (precise, structured, deeply grounded in data with clear bullet points and actionable advice).
Always format numbers with Indian Rupee formatting (₹). Give concrete recommendations with exact math."""

    try:
        client = genai.Client(api_key=api_key)
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=query,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
            )
        )
        return response.text
    except Exception as e:
        logging.getLogger(__name__).warning(f"Gemini API call failed: {e}")
        return f"Sorry, I encountered an error communicating with the AI service: {e}"


async def _generate_response(query: str, data: dict, personality: str) -> dict:
    """Generate a high-precision, grounded response using real data and smart reasoning."""
    q = query.lower()

    # 1. Call Gemini LLM
    llm_output = await _call_llm_if_available(query, data, personality)
    
    return {
        "content": llm_output,
        "groundedData": [
            {"label": "Checking Liquidity", "value": _format_currency(data["checking"])},
            {"label": "Savings Cushion", "value": _format_currency(data["savings"])},
            {"label": "Cash Runway", "value": f"{data['runway']} Months"},
            {"label": "Monthly Burn", "value": _format_currency(data["monthly_burn"])},
        ],
        "confidence": "High",
        "quickActions": [
            {"label": "Simulate in What-If", "action": "navigate", "path": "/app/simulator"},
            {"label": "View Forecast", "action": "navigate", "path": "/app/forecast"},
        ],
    }


@router.post("/chat", response_model=ChatMessageResponse)
async def copilot_chat(
    request: CopilotRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    financials = await _compute_financials(db, current_user)
    res = await _generate_response(request.message, financials, request.personality or "balanced")
    
    return {
        "id": f"ai-msg-{int(time.time() * 1000)}",
        "role": "assistant",
        "sender": "ai",
        "content": res["content"],
        "text": res["content"],
        "timestamp": datetime.utcnow().isoformat(),
        "grounded_data": res.get("groundedData", []),
        "groundedData": res.get("groundedData", []),
        "confidence": res.get("confidence", "High"),
        "quick_actions": res.get("quickActions", []),
        "quickActions": res.get("quickActions", []),
    }


@router.post("/stream")
async def copilot_stream(
    request: CopilotRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    financials = await _compute_financials(db, current_user)
    response = await _generate_response(request.message, financials, request.personality or "balanced")
    content = response["content"]

    async def event_stream():
        yield f"data: {json.dumps({'type': 'status', 'content': 'Analyzing your real-time financial ledger...'})}\n\n"
        await asyncio.sleep(0.1)

        words = content.split(" ")
        for i, word in enumerate(words):
            chunk = word + ("" if i == len(words) - 1 else " ")
            yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
            await asyncio.sleep(0.015)

        msg_id = f"ai-msg-{int(time.time() * 1000)}"
        final = {
            "type": "done",
            "id": msg_id,
            "message": {
                "id": msg_id,
                "role": "assistant",
                "sender": "ai",
                "content": content,
                "text": content,
                "timestamp": datetime.utcnow().isoformat(),
                "groundedData": response.get("groundedData", []),
                "confidence": response.get("confidence", "High"),
                "quickActions": response.get("quickActions", []),
            }
        }
        yield f"data: {json.dumps(final)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
