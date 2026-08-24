"""Tests for base forecaster and evaluation metrics."""
import numpy as np
import pandas as pd
import pytest
from app.ml.forecasting.v2.base import BaseForecaster, ForecastPoint, ForecastResult


class DummyForecaster(BaseForecaster):
    """Simple forecaster for testing the base class."""
    name = "dummy"

    def fit(self, df, **kwargs):
        self._mean = df["y"].mean()
        return self

    def predict(self, horizon_days, **kwargs):
        dates = pd.date_range("2026-01-01", periods=horizon_days, freq="D")
        return pd.DataFrame({
            "ds": dates,
            "yhat": [self._mean] * horizon_days,
            "yhat_lower": [self._mean * 0.9] * horizon_days,
            "yhat_upper": [self._mean * 1.1] * horizon_days,
        })


@pytest.fixture
def sample_df():
    dates = pd.date_range("2025-01-01", periods=100, freq="D")
    np.random.seed(42)
    return pd.DataFrame({"ds": dates, "y": np.random.normal(100, 15, 100)})


class TestBaseForecaster:
    def test_evaluate_perfect_predictions(self):
        f = DummyForecaster()
        actual = pd.Series([100.0, 200.0, 300.0])
        predicted = pd.Series([100.0, 200.0, 300.0])
        metrics = f.evaluate(actual, predicted)
        assert metrics["mape"] == 0.0
        assert metrics["rmse"] == 0.0
        assert metrics["mae"] == 0.0

    def test_evaluate_imperfect_predictions(self):
        f = DummyForecaster()
        actual = pd.Series([100.0, 200.0, 300.0])
        predicted = pd.Series([110.0, 190.0, 310.0])
        metrics = f.evaluate(actual, predicted)
        assert 0 < metrics["mape"] < 1
        assert metrics["rmse"] > 0
        assert metrics["mae"] > 0

    def test_evaluate_handles_zeros(self):
        f = DummyForecaster()
        actual = pd.Series([0.0, 100.0, 200.0])
        predicted = pd.Series([10.0, 110.0, 190.0])
        metrics = f.evaluate(actual, predicted)
        assert isinstance(metrics["mape"], float)

    def test_dummy_fit_and_predict(self, sample_df):
        f = DummyForecaster()
        f.fit(sample_df)
        result = f.predict(30)
        assert len(result) == 30
        assert "ds" in result.columns
        assert "yhat" in result.columns
        assert "yhat_lower" in result.columns
        assert "yhat_upper" in result.columns

    def test_to_forecast_result(self, sample_df):
        f = DummyForecaster()
        f.fit(sample_df)
        pred = f.predict(14)
        result = f.to_forecast_result(pred, [0.5, 0.8, 0.95])
        assert isinstance(result, ForecastResult)
        assert len(result.points) == 14
        assert result.model_name == "dummy"
        for point in result.points:
            assert isinstance(point, ForecastPoint)
            assert point.date is not None
            assert isinstance(point.balance, float)
