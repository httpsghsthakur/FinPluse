import re

with open(r'backend\app\api\v1\forecast.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the simple daily_burn calculation with ProphetForecaster
old_logic = '''    # Calculate daily burn rate (average daily expenses excluding transfers and large anomalies)
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
    temp_balance = current_liquid
    historical_points = []
    for i in range(30, -1, -1):
        d = start_history + timedelta(days=i)
        historical_points.append({
            "date": d.isoformat(),
            "balance": round(temp_balance, 2)
        })
        temp_balance -= daily_flow[d]
    
    historical_points.reverse()
    points.extend(historical_points)

    # Forward projection (simple linear for now)
    future_balance = current_liquid
    for i in range(1, days + 1):
        d = today + timedelta(days=i)
        future_balance -= daily_burn
        points.append({
            "date": d.isoformat(),
            "balance": round(future_balance, 2)
        })'''

new_logic = '''    points: list[dict] = []
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
    temp_balance = current_liquid
    historical_points = []
    for i in range(30, -1, -1):
        d = start_history + timedelta(days=i)
        historical_points.append({
            "date": d.isoformat(),
            "balance": round(temp_balance, 2)
        })
        temp_balance -= daily_flow[d]
    
    historical_points.reverse()
    points.extend(historical_points)

    # Use Prophet for projection
    import pandas as pd
    from app.ml.forecasting.v2.prophet_forecaster import ProphetForecaster
    
    df_history = pd.DataFrame([
        {"ds": d, "y": flow} for d, flow in daily_flow.items()
    ])
    
    forecaster = ProphetForecaster()
    try:
        forecaster.fit(df_history)
        forecast_df = forecaster.predict(horizon_days=days)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Prophet failed: {e}. Falling back to linear.")
        total_expenses = sum(abs(tx.amount) for tx in history_txs if tx.amount < 0 and not tx.is_anomaly and tx.category_id != "cat-transfers")
        daily_burn = total_expenses / 30 if total_expenses > 0 else 115.0
        forecast_df = pd.DataFrame({
            "ds": [today + timedelta(days=i) for i in range(1, days + 1)],
            "yhat": [-daily_burn] * days,
            "yhat_lower": [-daily_burn * 1.2] * days,
            "yhat_upper": [-daily_burn * 0.8] * days
        })
        
    future_balance = current_liquid
    for _, row in forecast_df.iterrows():
        # Prophet predicts daily net flow
        future_balance += float(row["yhat"])
        upper_bound = future_balance + (float(row.get("yhat_upper", row["yhat"])) - float(row["yhat"]))
        lower_bound = future_balance - (float(row["yhat"]) - float(row.get("yhat_lower", row["yhat"])))
        
        points.append({
            "date": row["ds"].date().isoformat() if hasattr(row["ds"], "date") else str(row["ds"])[:10],
            "balance": round(future_balance, 2),
            "confidence_upper": round(upper_bound, 2),
            "confidence_lower": round(lower_bound, 2)
        })'''

text = text.replace(old_logic, new_logic)

with open(r'backend\app\api\v1\forecast.py', 'w', encoding='utf-8') as f:
    f.write(text)
