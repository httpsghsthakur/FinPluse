"""
Prophet Forecasting Service for FinPulse.

Performs point-in-time time-series trend forecasting with confidence intervals
using Facebook Prophet. Computes chronological hold-out evaluation metrics (MAE, RMSE).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class ProphetService:
    """Encapsulates time-series forecasting via Facebook Prophet."""

    @staticmethod
    def forecast(
        df: pd.DataFrame,
        horizon_days: int = 30,
        evaluate_holdout: bool = True,
        test_ratio: float = 0.2,
    ) -> Dict[str, Any]:
        """Fit Prophet on historical price data and project forward.
        
        Args:
            df: DataFrame containing at least 'timestamp' (or 'ds') and 'close' (or 'y').
            horizon_days: Number of days to forecast into the future.
            evaluate_holdout: Whether to compute chronological hold-out MAE/RMSE.
            test_ratio: Fraction of history to reserve for hold-out evaluation.
            
        Returns:
            Dict containing:
                - status: 'success' or 'error'
                - forecast: List of dicts with 'date', 'predicted', 'lower', 'upper'
                - metrics: Dict with 'mae', 'rmse', 'test_points' (if evaluated)
                - horizon_days: int
                - model: 'Facebook Prophet'
        """
        try:
            from prophet import Prophet
        except ImportError as e:
            logger.error(f"Prophet not installed: {e}")
            return {
                "status": "error",
                "message": "Prophet library is not installed in the environment.",
            }

        # Validate input dataframe
        if df is None or df.empty:
            return {"status": "error", "message": "Input dataframe is empty."}

        # Normalize column names for Prophet
        prophet_df = pd.DataFrame()
        date_col = "timestamp" if "timestamp" in df.columns else ("ds" if "ds" in df.columns else df.columns[0])
        val_col = "close" if "close" in df.columns else ("y" if "y" in df.columns else df.columns[1])

        prophet_df["ds"] = pd.to_datetime(df[date_col]).dt.tz_localize(None)
        prophet_df["y"] = pd.to_numeric(df[val_col], errors="coerce")
        prophet_df = prophet_df.dropna().sort_values(by="ds").reset_index(drop=True)

        if len(prophet_df) < 20:
            return {
                "status": "error",
                "message": f"Insufficient observations for Prophet ({len(prophet_df)} provided, minimum 20 required).",
            }

        metrics: Optional[Dict[str, Any]] = None

        # Chronological hold-out evaluation (strictly past -> future split)
        if evaluate_holdout and len(prophet_df) >= 30:
            split_idx = int(len(prophet_df) * (1.0 - test_ratio))
            train_sub = prophet_df.iloc[:split_idx]
            test_sub = prophet_df.iloc[split_idx:]

            try:
                eval_model = Prophet(
                    yearly_seasonality=len(train_sub) > 365,
                    weekly_seasonality=True,
                    daily_seasonality=False,
                    changepoint_prior_scale=0.05,
                    interval_width=0.80,
                )
                eval_model.fit(train_sub)

                future_eval = eval_model.make_future_dataframe(periods=len(test_sub), freq="D", include_history=False)
                pred_eval = eval_model.predict(future_eval)

                # Match test points
                y_true = test_sub["y"].values
                y_pred = pred_eval["yhat"].iloc[:len(y_true)].values

                mae = float(np.mean(np.abs(y_true - y_pred)))
                rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

                metrics = {
                    "mae": round(mae, 2),
                    "rmse": round(rmse, 2),
                    "test_points": int(len(y_true)),
                    "evaluation_period": f"{test_sub['ds'].iloc[0].strftime('%Y-%m-%d')} to {test_sub['ds'].iloc[-1].strftime('%Y-%m-%d')}",
                }
            except Exception as eval_err:
                logger.warning(f"Prophet evaluation calculation note: {eval_err}")

        # Train full model for future projection
        try:
            model = Prophet(
                yearly_seasonality=len(prophet_df) > 365,
                weekly_seasonality=True,
                daily_seasonality=False,
                changepoint_prior_scale=0.05,
                interval_width=0.80,
            )
            model.fit(prophet_df)

            # Generate future dataframe
            future = model.make_future_dataframe(periods=horizon_days, freq="D", include_history=False)
            forecast_raw = model.predict(future)

            forecast_points: List[Dict[str, Any]] = []
            for _, row in forecast_raw.iterrows():
                forecast_points.append({
                    "date": row["ds"].strftime("%Y-%m-%d"),
                    "predicted": round(float(row["yhat"]), 2),
                    "lower": round(float(row["yhat_lower"]), 2),
                    "upper": round(float(row["yhat_upper"]), 2),
                })

            last_close = float(prophet_df["y"].iloc[-1])
            final_pred = forecast_points[-1]["predicted"] if forecast_points else last_close
            trend_pct = ((final_pred - last_close) / last_close) * 100 if last_close != 0 else 0.0

            return {
                "status": "success",
                "model": "Facebook Prophet",
                "horizon_days": horizon_days,
                "history_points": len(prophet_df),
                "last_actual_price": round(last_close, 2),
                "projected_price": round(final_pred, 2),
                "projected_change_percent": round(trend_pct, 2),
                "forecast": forecast_points,
                "metrics": metrics,
            }

        except Exception as e:
            logger.error(f"Prophet training/prediction failed: {e}")
            return {
                "status": "error",
                "message": f"Prophet execution error: {str(e)}",
            }
