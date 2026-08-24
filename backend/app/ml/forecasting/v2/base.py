"""
Finpluse v2 — Abstract Base Forecaster

All forecasting models implement this interface so the ensemble
and training pipeline can treat them uniformly.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Optional, Sequence

import numpy as np
import pandas as pd


@dataclass
class ForecastRequest:
    """Input to any forecaster."""
    user_id: str
    historical_df: pd.DataFrame          # columns: date, amount, category_id, merchant
    horizon_days: int = 90
    confidence_levels: list[float] = field(default_factory=lambda: [0.5, 0.8, 0.95])
    current_balance: float = 0.0
    known_future_events: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ForecastPoint:
    """Single day forecast output."""
    date: str
    balance: float
    confidence_intervals: dict[float, tuple[float, float]] = field(default_factory=dict)


@dataclass
class ForecastResult:
    """Complete forecast output from any model."""
    points: list[ForecastPoint]
    model_name: str
    mape: float = 0.0
    rmse: float = 0.0
    last_trained: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseForecaster(abc.ABC):
    """Abstract base class for all Finpluse forecasting models."""

    name: str = "base"

    @abc.abstractmethod
    def fit(self, df: pd.DataFrame, **kwargs: Any) -> "BaseForecaster":
        """Train the model on historical daily balance/spending data.

        Args:
            df: DataFrame with columns ['ds' (date), 'y' (daily_net_amount)].
            **kwargs: Model-specific training arguments.

        Returns:
            Self for chaining.
        """
        ...

    @abc.abstractmethod
    def predict(self, horizon_days: int, **kwargs: Any) -> pd.DataFrame:
        """Generate point forecasts for the next ``horizon_days``.

        Args:
            horizon_days: Number of days to forecast.

        Returns:
            DataFrame with columns ['ds', 'yhat', 'yhat_lower', 'yhat_upper'].
        """
        ...

    def evaluate(self, actual: pd.Series, predicted: pd.Series) -> dict[str, float]:
        """Compute standard forecast accuracy metrics.

        Args:
            actual: Ground truth values.
            predicted: Model predictions aligned to same dates.

        Returns:
            Dict with 'mape', 'rmse', 'mae', 'smape' keys.
        """
        actual_arr = np.asarray(actual, dtype=np.float64)
        pred_arr = np.asarray(predicted, dtype=np.float64)

        # Avoid division by zero in MAPE
        mask = actual_arr != 0
        if mask.sum() == 0:
            mape = 0.0
        else:
            mape = float(np.mean(np.abs((actual_arr[mask] - pred_arr[mask]) / actual_arr[mask])))

        rmse = float(np.sqrt(np.mean((actual_arr - pred_arr) ** 2)))
        mae = float(np.mean(np.abs(actual_arr - pred_arr)))

        # Symmetric MAPE
        denom = np.abs(actual_arr) + np.abs(pred_arr)
        safe_denom = np.where(denom == 0, 1.0, denom)
        smape = float(np.mean(2.0 * np.abs(actual_arr - pred_arr) / safe_denom))

        return {"mape": round(mape, 6), "rmse": round(rmse, 2), "mae": round(mae, 2), "smape": round(smape, 6)}

    def to_forecast_result(self, predictions_df: pd.DataFrame, confidence_levels: list[float]) -> ForecastResult:
        """Convert raw predictions DataFrame to structured ForecastResult.

        Args:
            predictions_df: DataFrame with 'ds', 'yhat', and optional 'yhat_lower_X', 'yhat_upper_X' columns.
            confidence_levels: List of confidence levels (e.g. [0.5, 0.8, 0.95]).

        Returns:
            ForecastResult with typed ForecastPoint objects.
        """
        points: list[ForecastPoint] = []
        for _, row in predictions_df.iterrows():
            intervals: dict[float, tuple[float, float]] = {}
            for cl in confidence_levels:
                lower_col = f"yhat_lower_{cl}"
                upper_col = f"yhat_upper_{cl}"
                if lower_col in row and upper_col in row:
                    intervals[cl] = (float(row[lower_col]), float(row[upper_col]))
                else:
                    # Fallback: use default lower/upper columns with scaling
                    base_lower = row.get("yhat_lower", row["yhat"] * 0.9)
                    base_upper = row.get("yhat_upper", row["yhat"] * 1.1)
                    spread = (base_upper - base_lower) / 2
                    # Scale spread by confidence level ratio
                    scale = cl / 0.8 if 0.8 != 0 else 1.0
                    intervals[cl] = (
                        float(row["yhat"] - spread * scale),
                        float(row["yhat"] + spread * scale),
                    )
            ds_val = row["ds"]
            if isinstance(ds_val, (datetime, date, pd.Timestamp)):
                ds_str = ds_val.strftime("%Y-%m-%d")
            else:
                ds_str = str(ds_val)
            points.append(ForecastPoint(date=ds_str, balance=float(row["yhat"]), confidence_intervals=intervals))

        return ForecastResult(points=points, model_name=self.name, last_trained=datetime.utcnow().isoformat() + "Z")
