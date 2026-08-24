"""Tests for all forecasting model implementations."""
import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def training_data():
    """Generate synthetic daily financial data for testing."""
    np.random.seed(42)
    dates = pd.date_range("2025-06-01", periods=120, freq="D")
    # Simulate: base spending + weekly pattern + noise
    base = -150.0
    weekly = 30 * np.sin(2 * np.pi * np.arange(120) / 7)
    # Paydays on 1st and 15th
    payday = np.zeros(120)
    for i, d in enumerate(dates):
        if d.day in (1, 15):
            payday[i] = 3000
    noise = np.random.normal(0, 20, 120)
    y = base + weekly + payday + noise
    return pd.DataFrame({"ds": dates, "y": y})


class TestNBeatsForecaster:
    def test_fit_and_predict(self, training_data):
        from app.ml.forecasting.v2.nbeats_forecaster import NBeatsForecaster
        model = NBeatsForecaster(lookback_window=30, forecast_horizon=7, epochs=5, hidden_size=32)
        model.fit(training_data)
        result = model.predict(14)
        assert len(result) == 14
        assert "yhat" in result.columns
        assert not result["yhat"].isna().any()

    def test_predict_without_fit_raises(self):
        from app.ml.forecasting.v2.nbeats_forecaster import NBeatsForecaster
        model = NBeatsForecaster()
        with pytest.raises(RuntimeError):
            model.predict(7)

    def test_short_data_handling(self):
        from app.ml.forecasting.v2.nbeats_forecaster import NBeatsForecaster
        short = pd.DataFrame({"ds": pd.date_range("2025-01-01", periods=5, freq="D"), "y": [100]*5})
        model = NBeatsForecaster(lookback_window=30, forecast_horizon=7, epochs=2)
        model.fit(short)  # Should not crash
        result = model.predict(7)
        assert len(result) == 7


class TestNHitsForecaster:
    def test_fit_and_predict(self, training_data):
        from app.ml.forecasting.v2.nhits_forecaster import NHitsForecaster
        model = NHitsForecaster(lookback_window=30, forecast_horizon=7, epochs=5, hidden_size=32)
        model.fit(training_data)
        result = model.predict(14)
        assert len(result) == 14
        assert all(col in result.columns for col in ["ds", "yhat", "yhat_lower", "yhat_upper"])


class TestTFTForecaster:
    def test_fit_and_predict(self, training_data):
        from app.ml.forecasting.v2.tft_forecaster import TemporalFusionTransformerForecaster
        model = TemporalFusionTransformerForecaster(
            lookback_window=30, forecast_horizon=7, epochs=3, hidden_size=16
        )
        model.fit(training_data)
        result = model.predict(14)
        assert len(result) == 14


class TestQuantileForecaster:
    def test_wraps_base_model(self, training_data):
        from app.ml.forecasting.v2.nbeats_forecaster import NBeatsForecaster
        from app.ml.forecasting.v2.quantile_forecaster import QuantileForecaster
        base = NBeatsForecaster(lookback_window=30, forecast_horizon=7, epochs=3, hidden_size=32)
        quantile = QuantileForecaster(base, quantiles=(0.10, 0.50, 0.90))
        quantile.fit(training_data)
        result = quantile.predict(14)
        assert len(result) == 14
        assert "yhat_lower_0.1" in result.columns or "yhat_lower" in result.columns


class TestWeightedEnsemble:
    def test_fit_and_predict(self, training_data):
        from app.ml.forecasting.v2.nbeats_forecaster import NBeatsForecaster
        from app.ml.forecasting.v2.nhits_forecaster import NHitsForecaster
        from app.ml.forecasting.v2.ensemble import WeightedEnsemble

        models = [
            NBeatsForecaster(lookback_window=30, forecast_horizon=7, epochs=3, hidden_size=32),
            NHitsForecaster(lookback_window=30, forecast_horizon=7, epochs=3, hidden_size=32),
        ]
        ensemble = WeightedEnsemble(models)
        ensemble.fit(training_data)
        result = ensemble.predict(14)
        assert len(result) == 14
        weights = ensemble.get_model_weights()
        assert len(weights) == 2
        assert abs(sum(weights.values()) - 1.0) < 0.01

    def test_empty_models_raises(self):
        from app.ml.forecasting.v2.ensemble import WeightedEnsemble
        with pytest.raises(ValueError):
            WeightedEnsemble([])
