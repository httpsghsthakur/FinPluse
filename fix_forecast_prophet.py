import re

with open(r'backend\app\api\v1\forecast.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_logic = '''    # Future projected days
    running_balance = current_liquid

    for day in range(days + 1):
        future_date = today + timedelta(days=day)
        date_str = future_date.isoformat()
        day_events: list[dict] = []
        dom = future_date.day

        # Check recurring items
        for rec in recurring_items:
            # Simple check based on frequency (assuming monthly occurs on the same dom, biweekly every 14 days)
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

        # Subtract daily burn
        running_balance -= daily_burn
        uncertainty = day * 35

        points.append({
            "date": date_str,
            "actualBalance": round(current_liquid) if day == 0 else None,
            "forecastedBalance": round(running_balance),
            "lowerBound": round(running_balance - uncertainty),
            "upperBound": round(running_balance + uncertainty),
            "isActual": day == 0,
            "events": day_events,
        })'''

new_logic = '''    import pandas as pd
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
        })'''

text = text.replace(old_logic, new_logic)

with open(r'backend\app\api\v1\forecast.py', 'w', encoding='utf-8') as f:
    f.write(text)
