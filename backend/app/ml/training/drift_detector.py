"""
Finpluse v2 -- Data Drift Detector

Monitors feature distributions over time using Kolmogorov-Smirnov tests.
Triggers model retraining when distribution shift is detected (p < 0.05).
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DriftDetector:
    """Monitors statistical properties of feature distributions.

    Stores reference distribution snapshots and compares new data
    using two-sample KS test. Triggers retraining alerts when
    significant drift is detected.
    """

    def __init__(
        self,
        p_threshold: float = 0.05,
        reference_window_days: int = 60,
        detection_window_days: int = 14,
    ) -> None:
        """Initialize the drift detector.

        Args:
            p_threshold: KS test p-value threshold for declaring drift.
            reference_window_days: Days of data for reference distribution.
            detection_window_days: Days of recent data to test for drift.
        """
        self.p_threshold = p_threshold
        self.reference_window_days = reference_window_days
        self.detection_window_days = detection_window_days
        self._reference_stats: dict[str, dict[str, float]] = {}
        self._drift_history: list[dict[str, Any]] = []

    def set_reference(self, df: pd.DataFrame, features: list[str]) -> None:
        """Store reference distribution statistics.

        Args:
            df: Reference dataset.
            features: Column names to monitor.
        """
        for feat in features:
            if feat in df.columns:
                values = df[feat].dropna().values
                if len(values) > 0:
                    self._reference_stats[feat] = {
                        "mean": float(np.mean(values)),
                        "std": float(np.std(values)),
                        "median": float(np.median(values)),
                        "n_samples": len(values),
                    }
        logger.info(f"Reference distribution set for {len(self._reference_stats)} features")

    def check_drift(self, current_df: pd.DataFrame, reference_df: Optional[pd.DataFrame] = None) -> dict[str, Any]:
        """Check for distribution drift in current data.

        Args:
            current_df: Recent data to check.
            reference_df: Optional reference data. Uses stored stats if None.

        Returns:
            Dict with 'needs_retrain', 'drifted_features', and per-feature details.
        """
        from scipy import stats as sp_stats

        results: dict[str, Any] = {
            "needs_retrain": False,
            "drifted_features": [],
            "details": {},
            "checked_at": datetime.utcnow().isoformat() + "Z",
        }

        features_to_check = list(self._reference_stats.keys()) if not reference_df is None else []
        if reference_df is not None:
            features_to_check = [c for c in reference_df.columns if c in current_df.columns and np.issubdtype(current_df[c].dtype, np.number)]

        for feat in features_to_check:
            try:
                cur_vals = current_df[feat].dropna().values
                if len(cur_vals) < 5:
                    continue

                if reference_df is not None and feat in reference_df.columns:
                    ref_vals = reference_df[feat].dropna().values
                else:
                    continue

                if len(ref_vals) < 5:
                    continue

                stat, p_val = sp_stats.ks_2samp(ref_vals, cur_vals)
                has_drift = p_val < self.p_threshold

                results["details"][feat] = {
                    "ks_statistic": round(float(stat), 4),
                    "p_value": round(float(p_val), 6),
                    "has_drift": has_drift,
                }

                if has_drift:
                    results["drifted_features"].append(feat)
                    results["needs_retrain"] = True

            except Exception as e:
                logger.warning(f"Drift check failed for {feat}: {e}")

        if results["needs_retrain"]:
            self._drift_history.append(results)
            logger.warning(f"Drift detected in features: {results['drifted_features']}")

        return results

    def should_retrain(
        self,
        last_train_time: Optional[datetime] = None,
        n_new_transactions: int = 0,
        current_df: Optional[pd.DataFrame] = None,
        reference_df: Optional[pd.DataFrame] = None,
    ) -> tuple[bool, str]:
        """Determine if model retraining is needed.

        Checks three conditions:
        1. Scheduled: every 7 days since last training
        2. Event-driven: 50+ new transactions since last training
        3. Drift-based: KS test detects feature distribution shift

        Args:
            last_train_time: When the model was last trained.
            n_new_transactions: Count of new transactions since last training.
            current_df: Recent transaction data for drift detection.
            reference_df: Reference data for drift comparison.

        Returns:
            Tuple of (should_retrain: bool, reason: str).
        """
        # Check 1: Scheduled (every 7 days)
        if last_train_time is not None:
            days_since = (datetime.utcnow() - last_train_time).days
            if days_since >= 7:
                return True, f"Scheduled retrain (last trained {days_since} days ago)"

        # Check 2: Event-driven (50+ new transactions)
        if n_new_transactions >= 50:
            return True, f"Event-driven retrain ({n_new_transactions} new transactions)"

        # Check 3: Drift detection
        if current_df is not None and reference_df is not None:
            drift_result = self.check_drift(current_df, reference_df)
            if drift_result["needs_retrain"]:
                return True, f"Drift detected in: {drift_result['drifted_features']}"

        return False, "No retrain needed"
