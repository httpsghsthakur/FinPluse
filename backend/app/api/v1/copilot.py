"""AI Copilot endpoint — Phase 1: deterministic responses matching frontend aiEngine.
Phase 7 will replace this with actual LLM + function calling."""
from __future__ import annotations
from app.api.deps import get_current_user
from app.db.models.user import User

import time
import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.account import Account
from app.db.models.transaction import Transaction
from app.db.models.category import Category
from app.db.models.goal import Goal
from app.schemas.copilot import CopilotRequest, ChatMessageResponse

from app.ml.classifiers.intent_classifier import intent_classifier

router = APIRouter()


def _format_currency(amount: float) -> str:
    """Format currency for display."""
    sign = "-" if amount < 0 else ""
    return f"{sign}₹{abs(amount):,.2f}"


def _format_pct(value: float) -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.1f}%"


async def _compute_financials(db: AsyncSession, current_user: User) -> dict:
    """Compute live financial data from database."""
    # Accounts
    acc_result = await db.execute(
        select(Account).where(Account.user_id == current_user.id)
    )
    accounts = acc_result.scalars().all()
    checking = sum(a.balance for a in accounts if a.type == "checking")
    savings = sum(a.balance for a in accounts if a.type == "savings")
    credit = sum(a.balance for a in accounts if a.type == "credit")
    liquid = checking + savings
    net_worth = liquid + credit

    # Past 30 days transactions for metrics
    from datetime import datetime, timedelta, date
    today = date.today()
    start_30 = today - timedelta(days=30)
    
    tx_result = await db.execute(
        select(Transaction).where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.date >= start_30,
                Transaction.date <= today
            )
        )
    )
    recent_txs = tx_result.scalars().all()
    expense_txs = [t for t in recent_txs if t.amount < 0 and t.category_id != "cat-transfers"]
    income_txs = [t for t in recent_txs if t.amount > 0]
    total_expense = abs(sum(t.amount for t in expense_txs))
    total_income = sum(t.amount for t in income_txs)
    monthly_burn = total_expense if total_expense > 0 else 0
    runway = round(liquid / monthly_burn, 1) if monthly_burn > 0 else 0
    savings_rate = max(0.0, ((total_income - total_expense) / total_income * 100)) if total_income > 0 else 0.0

    # Category spending
    dining_spend = abs(sum(t.amount for t in expense_txs if t.category_id == "cat-dining"))
    grocery_spend = abs(sum(t.amount for t in expense_txs if t.category_id == "cat-groceries"))
    shopping_spend = abs(sum(t.amount for t in expense_txs if t.category_id == "cat-shopping"))

    # Goals
    goal_result = await db.execute(
        select(Goal).where(Goal.user_id == current_user.id)
    )
    goals = goal_result.scalars().all()

    # Dining budget
    cat_result = await db.execute(
        select(Category).where(Category.id == "cat-dining", Category.user_id == current_user.id)
    )
    dining_cat = cat_result.scalar_one_or_none()
    dining_budget = dining_cat.monthly_budget if dining_cat else 0

    return {
        "checking": checking, "savings": savings, "credit": credit,
        "liquid": liquid, "net_worth": net_worth,
        "total_expense": total_expense, "total_income": total_income,
        "monthly_burn": monthly_burn, "runway": runway, "savings_rate": savings_rate,
        "dining_spend": dining_spend, "dining_budget": dining_budget,
        "grocery_spend": grocery_spend, "shopping_spend": shopping_spend,
        "goals": goals, "accounts": accounts, "tx_count": len(recent_txs),
    }


def _generate_response(query: str, data: dict, personality: str) -> dict:
    """Generate a grounded AI response based on computed financial data."""
    q = query.lower()
    intent = intent_classifier.predict(query)

    if intent == "AFFORD":
        import re
        match = re.search(r"₹?([\d,]+)", q)
        amount = float(match.group(1).replace(",", "")) if match else 6500
        post = data["checking"] - amount
        safe = post > 25000

        return {
            "content": f"### Affordability Assessment for {_format_currency(amount)}\n\n"
                       f"1. **Checking Liquidity**: {_format_currency(data['checking'])}\n"
                       f"2. **After Purchase**: {_format_currency(post)}\n"
                       f"3. **Recommendation**: {'**Comfortable to proceed.** Your savings backup ensures runway.' if safe else '**Exercise caution.** Consider waiting for next paycheck.'}",
            "groundedData": [
                {"label": "Proposed Item", "value": _format_currency(amount)},
                {"label": "Checking Balance", "value": _format_currency(data["checking"])},
                {"label": "HYSA Backup", "value": _format_currency(data["savings"])},
                {"label": "Monthly Burn Rate", "value": _format_currency(data["monthly_burn"])},
            ],
            "confidence": "High",
            "quickActions": [
                {"label": "Simulate Purchase Impact", "action": "navigate", "path": "/app/simulator"},
                {"label": "Check Upcoming Bills", "action": "navigate", "path": "/app"},
            ],
        }

    if intent == "SPENDING":
        over = data["dining_spend"] > data["dining_budget"]
        return {
            "content": f"### Monthly Spending & Category Health\n\n"
                       f"- **Dining & Drinks**: **{_format_currency(data['dining_spend'])}** "
                       f"({'Over budget by ' + _format_currency(data['dining_spend'] - data['dining_budget']) if over else 'Within limit'})\n"
                       f"- **Groceries**: **{_format_currency(data['grocery_spend'])}**\n"
                       f"- **Shopping**: **{_format_currency(data['shopping_spend'])}**\n"
                       f"- **Total Discretionary**: **{_format_currency(data['total_expense'])}**",
            "groundedData": [
                {"label": "30-Day Outflows", "value": _format_currency(data["total_expense"])},
                {"label": "Dining Spend", "value": _format_currency(data["dining_spend"])},
                {"label": "Dining Budget", "value": _format_currency(data["dining_budget"])},
                {"label": "Savings Rate", "value": _format_pct(data["savings_rate"])},
            ],
            "confidence": "High",
            "quickActions": [
                {"label": "Open Budgets", "action": "navigate", "path": "/app/budgets"},
                {"label": "View Transactions", "action": "navigate", "path": "/app/transactions"},
            ],
        }

    if intent == "NET_WORTH":
        return {
            "content": f"### Net Worth & Runway Diagnostics\n\n"
                       f"- **Net Worth**: **{_format_currency(data['net_worth'])}** (+4.2% MoM)\n"
                       f"- **Liquid Cash**: **{_format_currency(data['liquid'])}**\n"
                       f"- **Credit Liability**: **{_format_currency(abs(data['credit']))}**\n"
                       f"- **Cash Runway**: **{data['runway']} months**",
            "groundedData": [
                {"label": "Net Worth", "value": _format_currency(data["net_worth"])},
                {"label": "Liquid Cash", "value": _format_currency(data["liquid"])},
                {"label": "Monthly Burn", "value": _format_currency(data["monthly_burn"])},
                {"label": "Runway", "value": f"{data['runway']} Months"},
            ],
            "confidence": "High",
            "quickActions": [
                {"label": "Open Cash Flow Forecast", "action": "navigate", "path": "/app/forecast"},
            ],
        }

    if intent == "GOALS":
        lines = []
        for g in data["goals"]:
            pct = round((g.current_amount / g.target_amount) * 100)
            remaining = g.target_amount - g.current_amount
            months_left = round(remaining / (g.monthly_contribution or 100), 1)
            lines.append(
                f"- **{g.name}**: **{_format_currency(g.current_amount)}** of "
                f"{_format_currency(g.target_amount)} ({pct}%) — ETA ~{months_left} months"
            )
        return {
            "content": f"### Savings Goals Trajectory\n\n" + "\n".join(lines),
            "groundedData": [
                {"label": "Active Goals", "value": str(len(data["goals"]))},
                {"label": "Total Saved", "value": _format_currency(sum(g.current_amount for g in data["goals"]))},
                {"label": "Monthly Contributions", "value": _format_currency(sum(g.monthly_contribution for g in data["goals"]))},
            ],
            "confidence": "High",
            "quickActions": [
                {"label": "Manage Goals", "action": "navigate", "path": "/app/goals"},
            ],
        }

    # Default
    return {
        "content": f"### Finpluse AI Financial Assessment\n\n"
                   f"- **Net Worth**: **{_format_currency(data['net_worth'])}**\n"
                   f"- **Liquidity**: **{_format_currency(data['liquid'])}** ({data['runway']} months runway)\n"
                   f"- **Savings Rate**: **{data['savings_rate']:.1f}%**\n\n"
                   f"Ask me about specific transactions, scenarios, or goal projections!",
        "groundedData": [
            {"label": "Net Worth", "value": _format_currency(data["net_worth"])},
            {"label": "Runway", "value": f"{data['runway']} Mo"},
            {"label": "Transactions", "value": str(data["tx_count"])},
            {"label": "Accounts", "value": str(len(data["accounts"]))},
        ],
        "confidence": "High",
        "quickActions": [
            {"label": "Explore Simulator", "action": "navigate", "path": "/app/simulator"},
            {"label": "View Insights", "action": "navigate", "path": "/app/insights"},
        ],
    }


@router.post("/stream")
async def copilot_stream(
    request: CopilotRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """SSE streaming copilot response.
    
    Phase 1: Deterministic grounded responses using DB data.
    Phase 7: Full LLM + function calling with streaming.
    """
    financials = await _compute_financials(db, current_user)
    response = _generate_response(request.message, financials, request.personality or "balanced")
    content = response["content"]

    async def event_stream():
        # Stream thinking status
        yield f"data: {json.dumps({'type': 'status', 'content': 'Analyzing your financial data...'})}\n\n"
        await asyncio.sleep(0.2)

        # Stream content word by word
        words = content.split(" ")
        for i, word in enumerate(words):
            chunk = word + ("" if i == len(words) - 1 else " ")
            yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
            await asyncio.sleep(0.02 + 0.015 * (hash(word) % 3))

        # Send final structured message
        msg_id = f"ai-msg-{int(time.time() * 1000)}"
        final = {
            "type": "complete",
            "message": {
                "id": msg_id,
                "role": "assistant",
                "sender": "ai",
                "content": content,
                "text": content,
                "timestamp": datetime.utcnow().isoformat(),
                "groundedData": response.get("groundedData", []),
                "confidence": response.get("confidence", "High"),
                "confidenceBand": response.get("confidence", "high").lower(),
                "confidenceScore": 0.96 if response.get("confidence") == "High" else 0.82,
                "quickActions": response.get("quickActions", []),
            },
        }
        yield f"data: {json.dumps(final)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat", response_model=ChatMessageResponse)
async def copilot_chat(
    request: CopilotRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Non-streaming copilot response."""
    financials = await _compute_financials(db, current_user)
    response = _generate_response(request.message, financials, request.personality or "balanced")

    return {
        "id": f"ai-msg-{int(time.time() * 1000)}",
        "role": "assistant",
        "sender": "ai",
        "content": response["content"],
        "text": response["content"],
        "timestamp": datetime.utcnow().isoformat(),
        "groundedData": response.get("groundedData", []),
        "confidence": response.get("confidence", "High"),
        "confidenceBand": response.get("confidence", "high").lower(),
        "confidenceScore": 0.96,
        "quickActions": response.get("quickActions", []),
    }
