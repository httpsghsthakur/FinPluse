"""Forecast endpoints — cash-flow projection matching frontend ForecastPoint contract."""
from __future__ import annotations

from datetime import datetime, timedelta, date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.account import Account
from app.db.models.transaction import Transaction
from app.db.models.recurring import RecurringTransaction
from app.db.models.goal import Goal
from app.schemas.forecast import ForecastResponse, ForecastPointResponse, ForecastEventResponse
from app.api.deps import get_current_user
from app.db.models.user import User


router = APIRouter()

@router.get("", response_model=ForecastResponse)

async def get_forecast(
    days: int = Query(default=90, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate cash-flow forecast matching frontend's getForecast().
    Dynamically computes based on real historical transactions and recurring bills.
    """
    # Get account balances
    result = await db.execute(
        select(Account).where(Account.user_id == current_user.id)
    )
    accounts = result.scalars().all()

    total_checking = sum(a.balance for a in accounts if a.type == "checking")
    total_savings = sum(a.balance for a in accounts if a.type == "savings")
    current_liquid = total_checking + total_savings

    today = datetime.now().date()
    start_history = today - timedelta(days=30)
    
    # Get all transactions from last 30 days
    tx_result = await db.execute(
        select(Transaction).where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.date >= start_history,
                Transaction.date <= today
            )
        ).order_by(Transaction.date.asc())
    )
    history_txs = tx_result.scalars().all()
    
    # Calculate daily burn rate (average daily expenses excluding transfers and large anomalies)
    total_expenses = sum(abs(tx.amount) for tx in history_txs if tx.amount < 0 and not tx.is_anomaly and tx.category_id != "cat-transfers")
    daily_burn = total_expenses / 30 if total_expenses > 0 else 115.0

    points: list[dict] = []
    events: list[dict] = []
    
    # Calculate daily net flow for past 30 days
    daily_flow = {start_history + timedelta(days=i): 0.0 for i in range(31)}
    for tx in history_txs:
        if isinstance(tx.date, datetime):
            d = tx.date.date()
        else:
            d = tx.date
        if d in daily_flow:
            daily_flow[d] += tx.amount

    # Backwards compute historical balances
    # If today's balance is current_liquid, yesterday's was current_liquid - today's net flow
    historical_balances = {today: current_liquid}
    running_back = current_liquid
    for i in range(1, 31):
        d = today - timedelta(days=i)
        d_next = today - timedelta(days=i-1)
        running_back -= daily_flow.get(d_next, 0)
        historical_balances[d] = running_back

    # Add historical points
    for i in range(30, 0, -1):
        d = today - timedelta(days=i)
        bal = historical_balances.get(d, current_liquid)
        points.append({
            "date": d.isoformat(),
            "actualBalance": round(bal),
            "forecastedBalance": round(bal),
            "lowerBound": round(bal * 0.98),
            "upperBound": round(bal * 1.02),
            "isActual": True,
            "events": [],
        })

    # Fetch Recurring Transactions for Future Projection
    rec_result = await db.execute(
        select(RecurringTransaction).where(
            and_(
                RecurringTransaction.user_id == current_user.id,
                RecurringTransaction.is_active == True
            )
        )
    )
    recurring_items = rec_result.scalars().all()
    
    # Fetch active Goals for auto-contributions
    goal_result = await db.execute(
        select(Goal).where(
            and_(
                Goal.user_id == current_user.id,
                Goal.is_completed == False,
                Goal.monthly_contribution > 0
            )
        )
    )
    active_goals = goal_result.scalars().all()

    import pandas as pd
    from app.ml.forecasting.v2.prophet_forecaster import ProphetForecaster
    
    # Use Prophet for projection
    df_history = pd.DataFrame([
        {"ds": str(d), "y": flow} for d, flow in daily_flow.items()
    ])
    
    forecaster = ProphetForecaster()
    try:
        if len(df_history) >= 10:
            forecaster.fit(df_history)
            forecast_df = forecaster.predict(horizon_days=days)
        else:
            raise ValueError("Not enough data")
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Prophet failed: {e}. Falling back to linear.")
        # Fallback to linear negative burn
        forecast_df = pd.DataFrame({
            "ds": pd.date_range(today, periods=days+1).tolist(),
            "yhat": [-daily_burn] * (days+1),
            "yhat_lower": [-daily_burn * 1.2] * (days+1),
            "yhat_upper": [-daily_burn * 0.8] * (days+1)
        })
        
    running_balance = current_liquid

    for day in range(days + 1):
        future_date = today + timedelta(days=day)
        date_str = future_date.isoformat()
        day_events: list[dict] = []
        dom = future_date.day

        # Check recurring items
        for rec in recurring_items:
            # Simple check based on frequency
            is_occurrence = False
            if rec.frequency == "monthly" and rec.expected_next_date and dom == rec.expected_next_date.day:
                is_occurrence = True
            elif rec.frequency == "biweekly" and rec.expected_next_date:
                days_since = (future_date - rec.expected_next_date).days
                if days_since >= 0 and days_since % 14 == 0:
                    is_occurrence = True
            
            if is_occurrence:
                ev = {
                    "id": f"ev-rec-{rec.id}-{day}",
                    "date": date_str,
                    "type": "payday" if rec.expected_amount > 0 else "recurring_bill",
                    "title": rec.merchant,
                    "amount": rec.expected_amount,
                    "accountId": rec.account_id or "acc-checking",
                }
                day_events.append(ev)
                events.append(ev)
                running_balance += rec.expected_amount

        # Check goal contributions (assume 5th of month)
        if dom == 5:
            for g in active_goals:
                if g.monthly_contribution:
                    ev = {
                        "id": f"ev-goal-{g.id}-{day}",
                        "date": date_str,
                        "type": "goal_contrib",
                        "title": f"Auto Goal: {g.name}",
                        "amount": -g.monthly_contribution,
                        "accountId": g.linked_account_id or "acc-savings",
                    }
                    day_events.append(ev)
                    events.append(ev)
                    running_balance -= g.monthly_contribution

        # Prophet prediction for the day
        # Filter forecast_df for this day
        # forecast_df['ds'] is datetime
        pred = forecast_df[forecast_df['ds'].dt.date == future_date]
        if not pred.empty:
            daily_yhat = float(pred['yhat'].iloc[0])
            daily_lower = float(pred['yhat_lower'].iloc[0])
            daily_upper = float(pred['yhat_upper'].iloc[0])
        else:
            daily_yhat = -daily_burn
            daily_lower = -daily_burn * 1.2
            daily_upper = -daily_burn * 0.8
            
        running_balance += daily_yhat
        
        uncertainty_upper = daily_upper - daily_yhat
        uncertainty_lower = daily_yhat - daily_lower

        points.append({
            "date": date_str,
            "actualBalance": round(current_liquid) if day == 0 else None,
            "forecastedBalance": round(running_balance),
            "lowerBound": round(running_balance - uncertainty_lower),
            "upperBound": round(running_balance + uncertainty_upper),
            "isActual": day == 0,
            "events": day_events,
        })

    return {"points": points, "events": events}
