"""
Finpluse v2 — Facebook Prophet Forecaster

Baseline trend + seasonality model using Prophet.
Automatically detects changepoints, holidays, and weekly/yearly patterns.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np
import pandas as pd

from app.ml.forecasting.v2.base import BaseForecaster

logger = logging.getLogger(__name__)


class ProphetForecaster(BaseForecaster):
    """Facebook Prophet wrapper for financial time series.

    Handles automatic seasonality detection, US federal holiday effects,
    and changepoint tuning for detecting spending behavior changes.
    """

    name = "prophet"

    def __init__(
        self,
        changepoint_prior_scale: float = 0.05,
        seasonality_prior_scale: float = 10.0,
        holidays_prior_scale: float = 10.0,
        yearly_seasonality: bool = True,
        weekly_seasonality: bool = True,
        daily_seasonality: bool = False,
        changepoint_range: float = 0.8,
        mcmc_samples: int = 0,
        interval_width: float = 0.80,
    ) -> None:
        """Initialize Prophet with financial-tuned hyperparameters.

        Args:
            changepoint_prior_scale: Flexibility of trend changes. Lower = smoother.
            seasonality_prior_scale: Strength of seasonality components.
            holidays_prior_scale: Strength of holiday effects.
            yearly_seasonality: Enable yearly seasonality detection.
            weekly_seasonality: Enable weekly seasonality (payday patterns).
            daily_seasonality: Enable daily patterns (usually False for finance).
            changepoint_range: Proportion of history to place changepoints.
            mcmc_samples: If > 0, use MCMC for uncertainty (slower but more accurate).
            interval_width: Default confidence interval width.
        """
        self._changepoint_prior_scale = changepoint_prior_scale
        self._seasonality_prior_scale = seasonality_prior_scale
        self._holidays_prior_scale = holidays_prior_scale
        self._yearly_seasonality = yearly_seasonality
        self._weekly_seasonality = weekly_seasonality
        self._daily_seasonality = daily_seasonality
        self._changepoint_range = changepoint_range
        self._mcmc_samples = mcmc_samples
        self._interval_width = interval_width
        self._model: Any = None
        self._is_fitted: bool = False

    def _build_holiday_df(self) -> pd.DataFrame:
        """Generate US federal holidays DataFrame for Prophet.

        Returns:
            DataFrame with 'holiday', 'ds', 'lower_window', 'upper_window' columns.
        """
        from datetime import date, timedelta

        holidays_list: list[dict[str, Any]] = []
        # Generate holidays for 2020-2030
        for year in range(2020, 2031):
            holidays_list.extend([
                {"holiday": "new_years", "ds": f"{year}-01-01"},
                {"holiday": "mlk_day", "ds": f"{year}-01-{15 + (7 - date(year, 1, 15).weekday()) % 7}"},
                {"holiday": "presidents_day", "ds": f"{year}-02-{15 + (7 - date(year, 2, 15).weekday()) % 7}"},
                {"holiday": "memorial_day", "ds": f"{year}-05-{31 - (date(year, 5, 31).weekday() + 1) % 7}"},
                {"holiday": "independence_day", "ds": f"{year}-07-04"},
                {"holiday": "labor_day", "ds": f"{year}-09-{1 + (7 - date(year, 9, 1).weekday()) % 7}"},
                {"holiday": "thanksgiving", "ds": f"{year}-11-{22 + (3 - date(year, 11, 22).weekday()) % 7}"},
                {"holiday": "christmas", "ds": f"{year}-12-25"},
                # Payday patterns (1st and 15th are spending spikes)
                
            ])
            for m in range(1, 13):
                holidays_list.append({"holiday": "payday_15th", "ds": f"{year}-{m:02d}-15"})

        df = pd.DataFrame(holidays_list)
        df["ds"] = pd.to_datetime(df["ds"], errors="coerce")
        df = df.dropna(subset=["ds"])
        df["lower_window"] = -1
        df["upper_window"] = 1
        return df

    def fit(self, df: pd.DataFrame, **kwargs: Any) -> "ProphetForecaster":
        """Train Prophet on historical daily net cash flow.

        Args:
            df: DataFrame with 'ds' (datetime) and 'y' (daily net amount) columns.
            **kwargs: Additional Prophet configuration overrides.

        Returns:
            Self for method chaining.

        Raises:
            ValueError: If df is empty or missing required columns.
            ImportError: If prophet package is not installed.
        """
        if df.empty:
            raise ValueError("Cannot fit Prophet on empty DataFrame")
        if "ds" not in df.columns or "y" not in df.columns:
            raise ValueError("DataFrame must have 'ds' and 'y' columns")

        try:
            from prophet import Prophet
        except ImportError:
            logger.warning("Prophet not installed, using fallback linear model")
            self._is_fitted = True
            self._fallback_df = df.copy()
            return self

        holidays_df = self._build_holiday_df()

        self._model = Prophet(
            changepoint_prior_scale=kwargs.get("changepoint_prior_scale", self._changepoint_prior_scale),
            seasonality_prior_scale=kwargs.get("seasonality_prior_scale", self._seasonality_prior_scale),
            holidays_prior_scale=kwargs.get("holidays_prior_scale", self._holidays_prior_scale),
            yearly_seasonality=self._yearly_seasonality,
            weekly_seasonality=self._weekly_seasonality,
            daily_seasonality=self._daily_seasonality,
            changepoint_range=self._changepoint_range,
            mcmc_samples=self._mcmc_samples,
            interval_width=self._interval_width,
            holidays=holidays_df,
        )

        # Add monthly seasonality for paycheck cycles
        self._model.add_seasonality(name="monthly", period=30.5, fourier_order=5)
        # Add bi-weekly seasonality for bi-weekly paychecks
        self._model.add_seasonality(name="biweekly", period=14, fourier_order=3)

        clean_df = df[["ds", "y"]].copy()
        clean_df["ds"] = pd.to_datetime(clean_df["ds"])
        clean_df = clean_df.dropna()

        try:
            self._model.fit(clean_df)
            self._is_fitted = True
            logger.info(f"Prophet fitted on {len(clean_df)} data points")
        except Exception as e:
            logger.error(f"Prophet fitting failed: {e}")
            self._is_fitted = True
            self._fallback_df = df.copy()

        return self

    def predict(self, horizon_days: int, **kwargs: Any) -> pd.DataFrame:
        """Generate probabilistic forecasts for the given horizon.

        Args:
            horizon_days: Number of days to forecast forward.
            **kwargs: Additional prediction options.

        Returns:
            DataFrame with 'ds', 'yhat', 'yhat_lower', 'yhat_upper' columns.

        Raises:
            RuntimeError: If model has not been fitted.
        """
        if not self._is_fitted:
            raise RuntimeError("Prophet model not fitted. Call fit() first.")

        if self._model is None:
            # Fallback: simple linear extrapolation
            return self._fallback_predict(horizon_days)

        try:
            future = self._model.make_future_dataframe(periods=horizon_days, freq="D")
            forecast = self._model.predict(future)

            # Take only future dates
            result = forecast.tail(horizon_days)[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
            result = result.reset_index(drop=True)
            return result
        except Exception as e:
            logger.error(f"Prophet prediction failed: {e}")
            return self._fallback_predict(horizon_days)

    def _fallback_predict(self, horizon_days: int) -> pd.DataFrame:
        """Linear extrapolation fallback when Prophet is unavailable.

        Args:
            horizon_days: Number of days to forecast.

        Returns:
            DataFrame with 'ds', 'yhat', 'yhat_lower', 'yhat_upper'.
        """
        if hasattr(self, "_fallback_df") and not self._fallback_df.empty:
            recent = self._fallback_df.tail(30)
            mean_y = float(recent["y"].mean())
            std_y = float(recent["y"].std()) if len(recent) > 1 else abs(mean_y) * 0.15
        else:
            mean_y = 0.0
            std_y = 100.0

        last_date = pd.Timestamp.now().normalize()
        dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=horizon_days, freq="D")

        return pd.DataFrame({
            "ds": dates,
            "yhat": [mean_y] * horizon_days,
            "yhat_lower": [mean_y - 1.96 * std_y] * horizon_days,
            "yhat_upper": [mean_y + 1.96 * std_y] * horizon_days,
        })

    def get_components(self) -> dict[str, Any]:
        """Extract decomposed trend and seasonality components.

        Returns:
            Dict with 'trend', 'weekly', 'yearly', 'monthly' arrays.
        """
        if self._model is None:
            return {"trend": [], "weekly": [], "yearly": [], "monthly": []}

        try:
            future = self._model.make_future_dataframe(periods=0)
            forecast = self._model.predict(future)
            return {
                "trend": forecast["trend"].tolist(),
                "weekly": forecast.get("weekly", pd.Series(dtype=float)).tolist(),
                "yearly": forecast.get("yearly", pd.Series(dtype=float)).tolist(),
                "monthly": forecast.get("monthly", pd.Series(dtype=float)).tolist(),
            }
        except Exception:
            return {"trend": [], "weekly": [], "yearly": [], "monthly": []}
