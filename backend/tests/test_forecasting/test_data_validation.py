"""Tests for data validation and quality checks."""
import numpy as np
import pandas as pd
import pytest
from app.ml.features.data_validation import (
    ForecastRequestSchema,
    DataQualityChecker,
)


class TestForecastRequestSchema:
    def test_valid_request(self):
        req = ForecastRequestSchema(
            user_id="user-123",
            horizon_days=90,
            confidence_levels=[0.5, 0.8, 0.95],
        )
        assert req.user_id == "user-123"
        assert req.horizon_days == 90
        assert req.confidence_levels == [0.5, 0.8, 0.95]

    def test_invalid_confidence_level(self):
        with pytest.raises(Exception):
            ForecastRequestSchema(
                user_id="user-123",
                confidence_levels=[0.5, 1.5],
            )

    def test_default_values(self):
        req = ForecastRequestSchema(user_id="user-123")
        assert req.horizon_days == 90
        assert len(req.confidence_levels) > 0
        assert len(req.scenarios) == 0


class TestDataQualityChecker:
    @pytest.fixture
    def checker(self):
        return DataQualityChecker()

    def test_valid_data(self, checker):
        df = pd.DataFrame({
            "date": pd.date_range("2025-01-01", periods=100, freq="D"),
            "amount": np.random.normal(0, 100, 100),
        })
        result = checker.validate(df)
        assert result["is_valid"]
        assert len(result["errors"]) == 0

    def test_empty_dataframe(self, checker):
        result = checker.validate(pd.DataFrame())
        assert not result["is_valid"]

    def test_missing_columns(self, checker):
        df = pd.DataFrame({"x": [1, 2, 3]})
        result = checker.validate(df)
        assert not result["is_valid"]

    def test_detects_outliers(self, checker):
        values = np.random.normal(100, 10, 100)
        values[50] = 10000  # Extreme outlier
        df = pd.DataFrame({
            "date": pd.date_range("2025-01-01", periods=100, freq="D"),
            "amount": values,
        })
        result = checker.validate(df)
        assert result["is_valid"]
        # Should warn about outlier
        assert any("outlier" in w.lower() for w in result["warnings"])
