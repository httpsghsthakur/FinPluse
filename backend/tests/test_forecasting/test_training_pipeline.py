"""Tests for the training pipeline."""
import numpy as np
import pandas as pd
import pytest
from app.ml.training.training_pipeline import TimeSeriesCrossValidator, TrainingPipeline


@pytest.fixture
def training_data():
    np.random.seed(42)
    dates = pd.date_range("2025-01-01", periods=200, freq="D")
    y = np.cumsum(np.random.normal(0, 10, 200)) + 1000
    return pd.DataFrame({"ds": dates, "y": y})


class TestTimeSeriesCrossValidator:
    def test_produces_correct_splits(self):
        cv = TimeSeriesCrossValidator(n_splits=5, gap=7)
        df = pd.DataFrame({
            "ds": pd.date_range("2025-01-01", periods=200, freq="D"),
            "y": range(200),
        })
        splits = cv.split(df)
        assert len(splits) >= 3
        for train, test in splits:
            assert len(train) > 0
            assert len(test) > 0
            # Train should come before test (no leakage)
            assert train.index.max() < test.index.min()

    def test_respects_gap(self):
        cv = TimeSeriesCrossValidator(n_splits=3, gap=7)
        df = pd.DataFrame({
            "ds": pd.date_range("2025-01-01", periods=100, freq="D"),
            "y": range(100),
        })
        splits = cv.split(df)
        for train, test in splits:
            gap = test.index.min() - train.index.max()
            assert gap >= 7


class TestTrainingPipeline:
    def test_train_and_evaluate(self, training_data):
        from app.ml.forecasting.v2.nbeats_forecaster import NBeatsForecaster
        pipeline = TrainingPipeline(n_optuna_trials=1, n_cv_folds=3)
        result = pipeline.train_and_evaluate(
            training_data,
            model_classes=[NBeatsForecaster],
        )
        assert "best_model" in result
        assert "all_results" in result
        assert "experiment_id" in result
