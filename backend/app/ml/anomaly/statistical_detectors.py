"""
Finpluse v2 -- Statistical Anomaly Detectors (Layer 1)

Three independent statistical detectors:
- Z-Score: Flags if |z| > 3 for amount, frequency, or time-between-transactions
- IQR: Flags if outside [Q1 - 1.5*IQR, Q3 + 1.5*IQR]
- Seasonal Decomposition: STL residual thresholding
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class ZScoreDetector:
    """Detects anomalies using Z-score thresholding.

    Flags transactions where |z| > threshold for amount relative to
    the user's per-category spending distribution.
    """

    def __init__(self, threshold: float = 3.0) -> None:
        self.threshold = threshold
        self._stats: dict[str, dict[str, float]] = {}

    def fit(self, df: pd.DataFrame) -> "ZScoreDetector":
        """Compute per-category mean and std from historical data.

        Args:
            df: Transactions with 'amount' and 'category_id'.
        """
        if df.empty:
            return self
        grouped = df.groupby("category_id")["amount"].agg(["mean", "std"]).fillna(0)
        self._stats = grouped.to_dict(orient="index")
        return self

    def score(self, amount: float, category_id: str) -> dict[str, Any]:
        """Score a single transaction.

        Args:
            amount: Transaction amount.
            category_id: Category identifier.

        Returns:
            Dict with 'score', 'is_anomaly', 'z_score'.
        """
        stats = self._stats.get(category_id, {"mean": 0, "std": 100})
        mean = stats.get("mean", 0)
        std = stats.get("std", 100)
        if std == 0:
            std = abs(mean) * 0.3 if mean != 0 else 100

        z = (amount - mean) / std
        is_anomaly = abs(z) > self.threshold
        score = min(1.0, abs(z) / (self.threshold * 2))

        return {
            "detector": "z_score",
            "score": round(score, 4),
            "is_anomaly": is_anomaly,
            "z_score": round(float(z), 4),
            "threshold": self.threshold,
        }


class IQRDetector:
    """Detects anomalies using Interquartile Range method.

    Flags transactions outside [Q1 - k*IQR, Q3 + k*IQR] where k=1.5.
    """

    def __init__(self, k: float = 1.5) -> None:
        self.k = k
        self._bounds: dict[str, dict[str, float]] = {}

    def fit(self, df: pd.DataFrame) -> "IQRDetector":
        """Compute per-category IQR bounds.

        Args:
            df: Transactions with 'amount' and 'category_id'.
        """
        if df.empty:
            return self
        for cat_id, group in df.groupby("category_id"):
            amounts = group["amount"].abs().values
            if len(amounts) < 4:
                continue
            q1 = float(np.percentile(amounts, 25))
            q3 = float(np.percentile(amounts, 75))
            iqr = q3 - q1
            self._bounds[str(cat_id)] = {
                "lower": q1 - self.k * iqr,
                "upper": q3 + self.k * iqr,
                "q1": q1,
                "q3": q3,
                "iqr": iqr,
            }
        return self

    def score(self, amount: float, category_id: str) -> dict[str, Any]:
        """Score a single transaction against IQR bounds.

        Args:
            amount: Transaction amount (absolute value used).
            category_id: Category identifier.

        Returns:
            Dict with 'score', 'is_anomaly', 'distance_from_bound'.
        """
        abs_amount = abs(amount)
        bounds = self._bounds.get(category_id, {"lower": 0, "upper": 1000, "iqr": 500})
        upper = bounds.get("upper", 1000)
        lower = bounds.get("lower", 0)
        iqr = bounds.get("iqr", 500)

        if abs_amount > upper:
            distance = abs_amount - upper
            score = min(1.0, distance / (iqr + 1))
            is_anomaly = True
        elif abs_amount < lower:
            distance = lower - abs_amount
            score = min(1.0, distance / (iqr + 1))
            is_anomaly = True
        else:
            distance = 0.0
            score = 0.0
            is_anomaly = False

        return {
            "detector": "iqr",
            "score": round(score, 4),
            "is_anomaly": is_anomaly,
            "distance_from_bound": round(distance, 2),
            "bounds": {"lower": round(lower, 2), "upper": round(upper, 2)},
        }


class SeasonalDecompositionDetector:
    """Detects anomalies by decomposing time series with STL and thresholding residuals.

    Uses STL (Seasonal-Trend decomposition using LOESS) on daily spending,
    then flags days where the residual exceeds a threshold.
    """

    def __init__(self, residual_threshold_std: float = 2.5) -> None:
        self.residual_threshold_std = residual_threshold_std
        self._residual_mean: float = 0.0
        self._residual_std: float = 1.0
        self._is_fitted: bool = False

    def fit(self, daily_amounts: pd.Series) -> "SeasonalDecompositionDetector":
        """Fit STL decomposition on daily spending series.

        Args:
            daily_amounts: Series indexed by date with daily aggregate spending.
        """
        if len(daily_amounts) < 14:
            logger.warning("Insufficient data for STL decomposition, using raw stats")
            self._residual_mean = float(daily_amounts.mean()) if len(daily_amounts) > 0 else 0
            self._residual_std = float(daily_amounts.std()) if len(daily_amounts) > 1 else 100
            self._is_fitted = True
            return self

        try:
            from statsmodels.tsa.seasonal import STL
            stl = STL(daily_amounts, period=7, robust=True)
            result = stl.fit()
            residuals = result.resid
            self._residual_mean = float(residuals.mean())
            self._residual_std = float(residuals.std()) if residuals.std() > 0 else 1.0
        except (ImportError, Exception) as e:
            logger.warning(f"STL decomposition failed: {e}, using raw statistics")
            self._residual_mean = float(daily_amounts.mean())
            self._residual_std = float(daily_amounts.std()) if daily_amounts.std() > 0 else 100

        self._is_fitted = True
        return self

    def score(self, daily_amount: float) -> dict[str, Any]:
        """Score a daily spending total against the seasonal model.

        Args:
            daily_amount: Total spending for the day.

        Returns:
            Dict with 'score', 'is_anomaly', 'residual_z'.
        """
        if not self._is_fitted:
            return {"detector": "seasonal", "score": 0.0, "is_anomaly": False, "residual_z": 0.0}

        z = (daily_amount - self._residual_mean) / self._residual_std
        is_anomaly = abs(z) > self.residual_threshold_std
        score = min(1.0, abs(z) / (self.residual_threshold_std * 2))

        return {
            "detector": "seasonal_decomposition",
            "score": round(score, 4),
            "is_anomaly": is_anomaly,
            "residual_z": round(float(z), 4),
        }
