import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.ml.forecasting.v2.prophet_forecaster import ProphetForecaster
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error

def generate_historical_data():
    np.random.seed(42)
    dates = pd.date_range(end=datetime.today(), periods=120).tolist()
    y = []
    for d in dates:
        burn = -100
        if d.weekday() >= 5:
            burn -= 50
        if d.day in [1, 15]:
            burn += 3000
        burn += np.random.normal(0, 20)
        y.append(burn)
    df = pd.DataFrame({"ds": dates, "y": y})
    return df

def test_prophet_mae():
    df = generate_historical_data()
    train_df = df.iloc[:-30]
    test_df = df.iloc[-30:]
    forecaster = ProphetForecaster(mcmc_samples=0)
    forecaster.fit(train_df)
    forecast = forecaster.predict(horizon_days=30)
    y_true = test_df['y'].values
    y_pred = forecast['yhat'].values
    mae = mean_absolute_error(y_true, y_pred)
    print(f"\n[Prophet Forecaster Metrics]")
    print(f"MAE (30-day holdout): ${mae:.2f}")

test_prophet_mae()
