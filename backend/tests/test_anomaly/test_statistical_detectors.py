"""Tests for statistical anomaly detectors."""
import numpy as np
import pandas as pd
import pytest
from app.ml.anomaly.statistical_detectors import ZScoreDetector, IQRDetector


@pytest.fixture
def transactions_df():
    np.random.seed(42)
    return pd.DataFrame({
        "amount": np.concatenate([np.random.normal(-50, 15, 100), np.random.normal(-200, 30, 100)]),
        "category_id": ["cat-food"] * 100 + ["cat-shopping"] * 100,
    })


class TestZScoreDetector:
    def test_fit_and_score_normal(self, transactions_df):
        detector = ZScoreDetector(threshold=3.0)
        detector.fit(transactions_df)
        result = detector.score(-55, "cat-food")
        assert not result["is_anomaly"]
        assert result["score"] < 0.5

    def test_detects_extreme_amount(self, transactions_df):
        detector = ZScoreDetector(threshold=3.0)
        detector.fit(transactions_df)
        result = detector.score(-500, "cat-food")
        assert result["is_anomaly"]
        assert result["score"] > 0.5

    def test_unknown_category_doesnt_crash(self, transactions_df):
        detector = ZScoreDetector()
        detector.fit(transactions_df)
        result = detector.score(-100, "cat-unknown")
        assert "score" in result


class TestIQRDetector:
    def test_fit_and_score_normal(self, transactions_df):
        detector = IQRDetector(k=1.5)
        detector.fit(transactions_df)
        result = detector.score(-55, "cat-food")
        assert not result["is_anomaly"]

    def test_detects_outlier(self, transactions_df):
        detector = IQRDetector(k=1.5)
        detector.fit(transactions_df)
        result = detector.score(-300, "cat-food")
        assert result["is_anomaly"]
