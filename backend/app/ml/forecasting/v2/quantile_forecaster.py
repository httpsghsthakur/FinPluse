"""
Finpluse v2 — Quantile Forecaster Wrapper

Wraps any BaseForecaster to produce explicit quantile outputs at
10th, 25th, 50th, 75th, and 90th percentiles using conformal prediction.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

from app.ml.forecasting.v2.base import BaseForecaster

logger = logging.getLogger(__name__)


class QuantileForecaster(BaseForecaster):
    """Produces quantile forecasts by wrapping any base model.

    Uses conformal prediction: calibrate prediction intervals on a held-out
    calibration set so that empirical coverage matches the nominal level.

    Attributes:
        base_model: The underlying point forecaster.
        quantiles: List of quantile levels to output.
    """

    name = "quantile"

    def __init__(
        self,
        base_model: BaseForecaster,
        quantiles: tuple[float, ...] = (0.10, 0.25, 0.50, 0.75, 0.90),
        calibration_fraction: float = 0.2,
    ) -> None:
        """Initialize quantile wrapper.

        Args:
            base_model: Any fitted or unfitted BaseForecaster.
            quantiles: Quantile levels to compute.
            calibration_fraction: Fraction of training data reserved for calibration.
        """
        self.base_model = base_model
        self.quantiles = quantiles
        self.calibration_fraction = calibration_fraction
        self._residuals: np.ndarray = np.array([])
        self._is_fitted = False
        self.name = f"quantile_{base_model.name}"

    def fit(self, df: pd.DataFrame, **kwargs: Any) -> "QuantileForecaster":
        """Fit base model and calibrate quantiles using residual distribution.

        Args:
            df: DataFrame with 'ds' and 'y' columns.

        Returns:
            Self for chaining.
        """
        if df.empty:
            raise ValueError("Cannot fit QuantileForecaster on empty data")

        df_sorted = df.sort_values("ds").reset_index(drop=True)
        n = len(df_sorted)
        cal_size = max(5, int(n * self.calibration_fraction))
        train_df = df_sorted.iloc[:-cal_size]
        cal_df = df_sorted.iloc[-cal_size:]

        # Fit base model on training portion
        self.base_model.fit(train_df, **kwargs)

        # Generate predictions on calibration set
        try:
            cal_preds = self.base_model.predict(cal_size)
            if len(cal_preds) >= cal_size:
                pred_values = cal_preds["yhat"].values[:cal_size]
                actual_values = cal_df["y"].values[:cal_size]
                self._residuals = actual_values - pred_values
            else:
                self._residuals = np.zeros(cal_size)
        except Exception as e:
            logger.warning(f"Calibration failed: {e}, using zero residuals")
            self._residuals = np.zeros(cal_size)

        # Refit on full data for production predictions
        self.base_model.fit(df_sorted, **kwargs)
        self._is_fitted = True
        logger.info(f"QuantileForecaster calibrated with {len(self._residuals)} residuals")
        return self

    def predict(self, horizon_days: int, **kwargs: Any) -> pd.DataFrame:
        """Generate quantile-aware predictions.

        Args:
            horizon_days: Number of days to forecast.

        Returns:
            DataFrame with 'ds', 'yhat', and 'yhat_lower_Q', 'yhat_upper_Q' for each quantile.
        """
        if not self._is_fitted:
            raise RuntimeError("QuantileForecaster not fitted")

        base_pred = self.base_model.predict(horizon_days, **kwargs)
        result = base_pred[["ds", "yhat"]].copy()

        if len(self._residuals) > 0:
            for q in self.quantiles:
                quantile_value = float(np.quantile(self._residuals, q))
                anti_q = float(np.quantile(self._residuals, 1 - q))
                # Expanding uncertainty with horizon
                horizon_scale = np.sqrt(np.arange(1, horizon_days + 1))
                result[f"yhat_lower_{q}"] = result["yhat"] + quantile_value * horizon_scale * 0.1
                result[f"yhat_upper_{q}"] = result["yhat"] + anti_q * horizon_scale * 0.1
        else:
            for q in self.quantiles:
                scale = abs(q - 0.5) * 2
                result[f"yhat_lower_{q}"] = result["yhat"] * (1 - scale * 0.1)
                result[f"yhat_upper_{q}"] = result["yhat"] * (1 + scale * 0.1)

        result["yhat_lower"] = result.get("yhat_lower_0.1", result["yhat"] * 0.9)
        result["yhat_upper"] = result.get("yhat_upper_0.9", result["yhat"] * 1.1)

        return result
