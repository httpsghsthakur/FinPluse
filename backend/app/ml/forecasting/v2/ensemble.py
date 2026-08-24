"""
Finpluse v2 — Weighted Ensemble Forecaster

Dynamically weights multiple forecasting models based on recent MAPE performance.
Weights are recomputed weekly using the last 30 days of holdout data.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

from app.ml.forecasting.v2.base import BaseForecaster, ForecastResult

logger = logging.getLogger(__name__)


class WeightedEnsemble(BaseForecaster):
    """Dynamically weighted ensemble of multiple forecasting models.

    Strategy:
        1. Each model produces independent forecasts.
        2. Weights are inversely proportional to recent MAPE.
        3. Weights are recomputed weekly on the last 30 days of data.
        4. Final forecast = weighted average of all model forecasts.
        5. Confidence intervals = union of individual model intervals, adjusted.
    """

    name = "weighted_ensemble"

    def __init__(self, models: list[BaseForecaster], weight_decay: float = 0.95) -> None:
        """Initialize ensemble with a list of forecasters.

        Args:
            models: List of BaseForecaster instances (unfitted or fitted).
            weight_decay: Exponential decay factor for weight history.
        """
        if not models:
            raise ValueError("Ensemble requires at least one model")
        self.models = models
        self.weight_decay = weight_decay
        self._weights: dict[str, float] = {m.name: 1.0 / len(models) for m in models}
        self._model_mapes: dict[str, list[float]] = {m.name: [] for m in models}
        self._is_fitted = False
        self._last_weight_update: datetime | None = None

    def fit(self, df: pd.DataFrame, **kwargs: Any) -> "WeightedEnsemble":
        """Fit all models and compute initial weights from holdout MAPE.

        Args:
            df: DataFrame with 'ds' and 'y' columns.

        Returns:
            Self for chaining.
        """
        if df.empty:
            raise ValueError("Cannot fit ensemble on empty data")

        df_sorted = df.sort_values("ds").reset_index(drop=True)

        # Split: train (first 80%) and holdout (last 20%)
        n = len(df_sorted)
        holdout_size = max(7, int(n * 0.2))
        train_df = df_sorted.iloc[:-holdout_size]
        holdout_df = df_sorted.iloc[-holdout_size:]

        if len(train_df) < 10:
            # Not enough data for holdout evaluation, fit all with equal weights
            for model in self.models:
                try:
                    model.fit(df_sorted, **kwargs)
                except Exception as e:
                    logger.warning(f"Model {model.name} failed to fit: {e}")
            self._is_fitted = True
            return self

        # Fit each model on training data, evaluate on holdout
        mapes: dict[str, float] = {}
        for model in self.models:
            try:
                model.fit(train_df, **kwargs)
                pred_df = model.predict(holdout_size)
                if len(pred_df) >= holdout_size:
                    metrics = model.evaluate(holdout_df["y"].values, pred_df["yhat"].values[:holdout_size])
                    mapes[model.name] = max(metrics["mape"], 0.001)  # Avoid zero division
                    self._model_mapes[model.name].append(mapes[model.name])
                    logger.info(f"  {model.name}: MAPE={metrics['mape']:.4f}, RMSE={metrics['rmse']:.2f}")
                else:
                    mapes[model.name] = 1.0
            except Exception as e:
                logger.warning(f"Model {model.name} evaluation failed: {e}")
                mapes[model.name] = 1.0

        # Compute inverse-MAPE weights
        self._update_weights(mapes)

        # Refit all models on full data for production predictions
        for model in self.models:
            try:
                model.fit(df_sorted, **kwargs)
            except Exception as e:
                logger.warning(f"Final fit for {model.name} failed: {e}")

        self._is_fitted = True
        self._last_weight_update = datetime.utcnow()
        logger.info(f"Ensemble weights: {self._weights}")
        return self

    def _update_weights(self, mapes: dict[str, float]) -> None:
        """Recompute weights inversely proportional to MAPE.

        Args:
            mapes: Dict mapping model name to recent MAPE value.
        """
        inv_mapes = {name: 1.0 / mape for name, mape in mapes.items()}
        total = sum(inv_mapes.values())
        if total > 0:
            self._weights = {name: inv / total for name, inv in inv_mapes.items()}
        else:
            n = len(self.models)
            self._weights = {m.name: 1.0 / n for m in self.models}

    def predict(self, horizon_days: int, **kwargs: Any) -> pd.DataFrame:
        """Generate weighted ensemble forecast.

        Args:
            horizon_days: Number of days to forecast.

        Returns:
            DataFrame with weighted average point forecast and expanded intervals.
        """
        if not self._is_fitted:
            raise RuntimeError("Ensemble not fitted")

        predictions: list[tuple[str, float, pd.DataFrame]] = []
        for model in self.models:
            weight = self._weights.get(model.name, 0.0)
            if weight <= 0:
                continue
            try:
                pred = model.predict(horizon_days, **kwargs)
                predictions.append((model.name, weight, pred))
            except Exception as e:
                logger.warning(f"Model {model.name} prediction failed: {e}")

        if not predictions:
            raise RuntimeError("All models failed to produce predictions")

        # Use first prediction's dates as reference
        ref_dates = predictions[0][2]["ds"]
        yhat = np.zeros(horizon_days)
        yhat_lower = np.full(horizon_days, float("inf"))
        yhat_upper = np.full(horizon_days, float("-inf"))

        total_weight = sum(w for _, w, _ in predictions)

        for name, weight, pred in predictions:
            normalized_weight = weight / total_weight
            n = min(len(pred), horizon_days)
            yhat[:n] += pred["yhat"].values[:n] * normalized_weight

            if "yhat_lower" in pred.columns:
                yhat_lower[:n] = np.minimum(yhat_lower[:n], pred["yhat_lower"].values[:n])
            if "yhat_upper" in pred.columns:
                yhat_upper[:n] = np.maximum(yhat_upper[:n], pred["yhat_upper"].values[:n])

        # Fallback if bounds weren't set
        yhat_lower = np.where(yhat_lower == float("inf"), yhat * 0.85, yhat_lower)
        yhat_upper = np.where(yhat_upper == float("-inf"), yhat * 1.15, yhat_upper)

        return pd.DataFrame({
            "ds": ref_dates[:horizon_days],
            "yhat": yhat,
            "yhat_lower": yhat_lower,
            "yhat_upper": yhat_upper,
        })

    def get_model_weights(self) -> dict[str, float]:
        """Return current model weights for transparency.

        Returns:
            Dict mapping model name to weight.
        """
        return dict(self._weights)

    def get_model_performance(self) -> dict[str, dict[str, Any]]:
        """Return recent performance metrics for each model.

        Returns:
            Dict with model names mapping to performance stats.
        """
        result: dict[str, dict[str, Any]] = {}
        for name, mapes in self._model_mapes.items():
            result[name] = {
                "weight": self._weights.get(name, 0.0),
                "recent_mape": mapes[-1] if mapes else None,
                "avg_mape": float(np.mean(mapes)) if mapes else None,
                "n_evaluations": len(mapes),
            }
        return result
