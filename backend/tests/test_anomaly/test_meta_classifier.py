"""Tests for the anomaly meta-classifier."""
import numpy as np
import pandas as pd
import pytest
from app.ml.anomaly.meta_classifier import AnomalyMetaClassifier


class TestAnomalyMetaClassifier:
    def test_predict_without_training(self):
        clf = AnomalyMetaClassifier()
        clf._is_fitted = True
        scores = {"z_score": 0.8, "iqr": 0.7, "isolation_forest": 0.6}
        result = clf.predict(scores)
        assert "probability" in result
        assert "severity" in result
        assert "fired_detectors" in result

    def test_high_scores_produce_anomaly(self):
        clf = AnomalyMetaClassifier()
        clf._is_fitted = True
        scores = {name: 0.9 for name in clf.DETECTOR_NAMES}
        result = clf.predict(scores)
        assert result["probability"] > 0.5
        assert result["severity"] in ("WARNING", "CRITICAL")

    def test_low_scores_not_anomaly(self):
        clf = AnomalyMetaClassifier()
        clf._is_fitted = True
        scores = {name: 0.05 for name in clf.DETECTOR_NAMES}
        result = clf.predict(scores)
        assert result["probability"] < 0.3

    def test_shap_explanation(self):
        clf = AnomalyMetaClassifier()
        clf._is_fitted = True
        clf._feature_importances = {n: 0.125 for n in clf.DETECTOR_NAMES}
        scores = {"z_score": 0.8, "isolation_forest": 0.6}
        result = clf.get_shap_explanation(scores)
        assert "shap_values" in result
