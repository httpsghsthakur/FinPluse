"""
Finpluse v2 -- Meta-Classifier for Multi-Layer Anomaly Detection

XGBoost stacking ensemble over all detector scores.
Produces final anomaly probability + which detectors fired.
Includes SHAP explainability.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class AnomalyMetaClassifier:
    """XGBoost meta-classifier combining scores from all anomaly detectors.

    Input: Scores from all layer detectors (Z-Score, IQR, Seasonal, IsolationForest,
           OneClassSVM, Autoencoder, LSTM, Transformer)
    Output: Final anomaly probability + detector attribution.
    """

    DETECTOR_NAMES = [
        "z_score", "iqr", "seasonal_decomposition",
        "isolation_forest", "one_class_svm", "autoencoder",
        "lstm_autoencoder", "transformer",
    ]

    def __init__(self) -> None:
        self._model: Any = None
        self._is_fitted = False
        self._feature_importances: dict[str, float] = {}

    def fit(self, scores_df: pd.DataFrame, labels: pd.Series) -> "AnomalyMetaClassifier":
        """Train meta-classifier on detector scores with known labels.

        Args:
            scores_df: DataFrame where each column is a detector's score.
            labels: Binary Series (1=fraud, 0=legitimate).
        """
        if scores_df.empty or len(scores_df) < 10:
            self._is_fitted = True
            return self

        try:
            from xgboost import XGBClassifier
            self._model = XGBClassifier(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.1,
                eval_metric="logloss",
                use_label_encoder=False,
                random_state=42,
            )
            self._model.fit(scores_df, labels)

            # Feature importances
            importances = self._model.feature_importances_
            for i, name in enumerate(scores_df.columns):
                self._feature_importances[name] = float(importances[i])

        except ImportError:
            logger.warning("XGBoost not available, using weighted average fallback")
            self._model = None
        except Exception as e:
            logger.warning(f"Meta-classifier training failed: {e}")
            self._model = None

        self._is_fitted = True
        return self

    def predict(self, detector_scores: dict[str, float]) -> dict[str, Any]:
        """Produce final anomaly probability from detector scores.

        Args:
            detector_scores: Dict mapping detector name to its anomaly score.

        Returns:
            Dict with 'probability', 'is_anomaly', 'fired_detectors', 'explanation'.
        """
        scores_list = [detector_scores.get(name, 0.0) for name in self.DETECTOR_NAMES]
        scores_array = np.array(scores_list).reshape(1, -1)

        if self._model is not None:
            try:
                proba = float(self._model.predict_proba(scores_array)[0, 1])
            except Exception:
                proba = float(np.mean(scores_list))
        else:
            # Weighted average fallback
            weights = [0.15, 0.10, 0.10, 0.20, 0.15, 0.10, 0.10, 0.10]
            proba = float(sum(s * w for s, w in zip(scores_list, weights)))

        fired = [name for name, score in detector_scores.items() if score > 0.5]

        # Generate explanation
        top_contributors = sorted(detector_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        explanation_parts = []
        for name, score in top_contributors:
            if score > 0.3:
                explanation_parts.append(f"{name} ({score:.2f})")
        explanation = f"Top detectors: {', '.join(explanation_parts)}" if explanation_parts else "No strong signals"

        return {
            "probability": round(proba, 4),
            "is_anomaly": proba > 0.5,
            "severity": "CRITICAL" if proba > 0.7 else ("WARNING" if proba > 0.5 else "INFO"),
            "fired_detectors": fired,
            "detector_scores": detector_scores,
            "explanation": explanation,
        }

    def get_shap_explanation(self, detector_scores: dict[str, float]) -> dict[str, Any]:
        """Generate SHAP-style feature attributions.

        Args:
            detector_scores: Dict of detector name to score.

        Returns:
            Dict with per-detector contribution to the final decision.
        """
        if self._model is None:
            return {"shap_values": {}, "method": "fallback"}

        try:
            import shap
            scores_array = np.array([detector_scores.get(n, 0) for n in self.DETECTOR_NAMES]).reshape(1, -1)
            explainer = shap.TreeExplainer(self._model)
            shap_values = explainer.shap_values(scores_array)

            contributions = {}
            for i, name in enumerate(self.DETECTOR_NAMES):
                contributions[name] = float(shap_values[0][i]) if len(shap_values.shape) == 2 else float(shap_values[1][0][i])

            return {"shap_values": contributions, "method": "tree_shap", "base_value": float(explainer.expected_value if isinstance(explainer.expected_value, float) else explainer.expected_value[1])}
        except (ImportError, Exception) as e:
            logger.debug(f"SHAP not available: {e}")
            return {
                "shap_values": {n: detector_scores.get(n, 0) * self._feature_importances.get(n, 0.125) for n in self.DETECTOR_NAMES},
                "method": "importance_weighted",
            }
