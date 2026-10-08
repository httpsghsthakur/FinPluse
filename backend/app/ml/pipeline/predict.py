"""
FinPulse AI — Directional Inference Wrapper.

Provides point-in-time single-sample inference for FastAPI endpoints.
Loads serialized XGBoost artifacts (supporting native Booster JSON and Joblib formats).
"""
from __future__ import annotations

import os
from typing import Dict, Any, List

import joblib
import pandas as pd
import xgboost as xgb
from app.core.logging import get_logger

logger = get_logger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
XGB_JSON_PATH = os.path.join(MODEL_DIR, "xgboost_direction.json")
XGB_JOBLIB_PATH = os.path.join(MODEL_DIR, "xgboost_direction.joblib")
LE_PATH = os.path.join(MODEL_DIR, "label_encoder.joblib")
FEATURES_PATH = os.path.join(MODEL_DIR, "features.joblib")


class DirectionPredictor:
    """Inference wrapper for the trained XGBoost model."""

    def __init__(self):
        self.model = None
        self.le = None
        self.features: List[str] | None = None
        self.load_artifacts()

    def load_artifacts(self):
        """Load trained model and preprocessing artifacts."""
        try:
            if os.path.exists(XGB_JOBLIB_PATH):
                self.model = joblib.load(XGB_JOBLIB_PATH)
            elif os.path.exists(XGB_JSON_PATH):
                self.model = xgb.XGBClassifier()
                self.model.load_model(XGB_JSON_PATH)

            if os.path.exists(LE_PATH):
                self.le = joblib.load(LE_PATH)
            if os.path.exists(FEATURES_PATH):
                self.features = joblib.load(FEATURES_PATH)
        except Exception as e:
            logger.warning(f"Direction predictor artifacts could not be loaded: {e}")

    def predict(self, current_features: Dict[str, float]) -> Dict[str, Any]:
        """Generate prediction for a single instrument's current features."""
        if self.model is None or self.le is None or self.features is None:
            return {
                "status": "error",
                "message": "Model artifacts not loaded. Train pipeline first."
            }

        try:
            # Construct single-row DataFrame with identical ordered feature columns
            row_data = {f: float(current_features.get(f, 0.0)) for f in self.features}
            x_input = pd.DataFrame([row_data])

            probs = self.model.predict_proba(x_input)[0]
            class_idx = int(self.model.predict(x_input)[0])
            direction = str(self.le.inverse_transform([class_idx])[0])

            return {
                "status": "success",
                "direction": direction,
                "probabilities": {
                    str(cls_name): round(float(probs[i]), 4)
                    for i, cls_name in enumerate(self.le.classes_)
                },
                "disclaimer": "Simulated prediction based on technical indicators. Not financial advice.",
            }
        except Exception as e:
            return {"status": "error", "message": f"Inference error: {e}"}


# Singleton instance for application use
direction_predictor = DirectionPredictor()
