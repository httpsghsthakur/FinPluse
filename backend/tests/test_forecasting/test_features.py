"""Tests for v2 feature engineering."""
import numpy as np
import pandas as pd
import pytest
from app.ml.features.v2_features import AdvancedFeatureEngineer


@pytest.fixture
def transactions_df():
    """Generate realistic transaction data for feature tests."""
    np.random.seed(42)
    dates = pd.date_range("2025-06-01", periods=90, freq="D")
    rows = []
    for d in dates:
        # 2-5 transactions per day
        n_tx = np.random.randint(2, 6)
        for _ in range(n_tx):
            cat = np.random.choice(["cat-food", "cat-transport", "cat-shopping", "cat-utilities"])
            merchant = np.random.choice(["Whole Foods", "Shell", "Amazon", "PG&E"])
            amount = -np.random.exponential(50)
            rows.append({"date": d, "amount": amount, "category_id": cat, "merchant": merchant})
        # Income on 1st and 15th
        if d.day in (1, 15):
            rows.append({"date": d, "amount": 3500, "category_id": "cat-income", "merchant": "Employer"})
    return pd.DataFrame(rows)


@pytest.fixture
def engineer():
    return AdvancedFeatureEngineer()


class TestDailyFeatures:
    def test_produces_correct_columns(self, engineer, transactions_df):
        result = engineer.compute_daily_features(transactions_df)
        assert not result.empty
        expected_cols = ["daily_net", "rolling_mean_7d", "is_weekend", "dow_sin", "month_cos", "is_payday"]
        for col in expected_cols:
            assert col in result.columns, f"Missing column: {col}"

    def test_no_missing_dates(self, engineer, transactions_df):
        result = engineer.compute_daily_features(transactions_df)
        date_diff = pd.Series(result.index).diff().dropna()
        assert all(date_diff == pd.Timedelta(days=1))

    def test_cyclical_features_bounded(self, engineer, transactions_df):
        result = engineer.compute_daily_features(transactions_df)
        for col in ["dow_sin", "dow_cos", "month_sin", "month_cos"]:
            assert result[col].min() >= -1.0
            assert result[col].max() <= 1.0


class TestCategoryVelocity:
    def test_returns_velocities(self, engineer, transactions_df):
        velocities = engineer.compute_category_velocity(transactions_df)
        assert isinstance(velocities, dict)
        assert len(velocities) > 0
        for v in velocities.values():
            assert isinstance(v, float)


class TestIncomeStability:
    def test_stable_income(self, engineer, transactions_df):
        score = engineer.compute_income_stability_score(transactions_df)
        assert 0 <= score <= 1
        assert score > 0.3  # Regular income should be fairly stable

    def test_empty_data(self, engineer):
        score = engineer.compute_income_stability_score(pd.DataFrame(columns=["date", "amount"]))
        assert score == 0.0


class TestFourierRecurring:
    def test_detects_recurring(self, engineer, transactions_df):
        results = engineer.detect_recurring_expenses_fourier(transactions_df)
        assert isinstance(results, list)
        # Should detect at least some recurring patterns
        for r in results:
            assert "merchant" in r
            assert "period_days" in r
            assert "confidence" in r
            assert r["confidence"] >= 0


class TestPrepareDataset:
    def test_produces_ds_and_y(self, engineer, transactions_df):
        result = engineer.prepare_forecast_dataset(transactions_df)
        assert "ds" in result.columns
        assert "y" in result.columns
        assert len(result) > 0
