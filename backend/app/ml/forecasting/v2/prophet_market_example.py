"""
Minimal working example of ProphetForecaster on market close data.
Demonstrates trend and forecast intervals using the sample market dataset.
"""
from __future__ import annotations

import os
import pandas as pd
from app.ml.forecasting.v2.prophet_forecaster import ProphetForecaster

def run_prophet_market_demo():
    sample_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
        "app", "ml", "pipeline", "data", "sample", "synthetic_market_dataset.parquet"
    )
    if not os.path.exists(sample_path):
        print(f"Sample dataset not found at {sample_path}. Run collect_data.py --synthetic first.")
        return

    df = pd.read_parquet(sample_path)
    instrument = "NSE_EQ|INE002A01018"  # RELIANCE
    inst_df = df[df["instrument_key"] == instrument].tail(180).reset_index()

    prophet_df = pd.DataFrame({
        "ds": inst_df["timestamp"],
        "y": inst_df["close"]
    })

    print(f"Fitting Prophet on {len(prophet_df)} observations of {instrument}...")
    forecaster = ProphetForecaster(mcmc_samples=0)
    forecaster.fit(prophet_df)

    forecast_df = forecaster.predict(horizon_days=5)
    print("\nProphet 5-Day Forward Price Projections:")
    print(forecast_df[["ds", "yhat", "yhat_lower", "yhat_upper"]].to_string(index=False))

if __name__ == "__main__":
    run_prophet_market_demo()
