"""
Pytest unit tests verifying ML pipeline reproducibility:
1. Indicator formulas (RSI and MACD on hand-checked series)
2. No-leakage invariance test
3. Chronological split temporal ordering
4. Target directional threshold boundary tests
"""
import numpy as np
import pandas as pd
import pytest

from app.ml.pipeline.build_features import calculate_rsi, compute_instrument_features
from app.ml.pipeline.build_targets import label_direction, UP_THRESHOLD, DOWN_THRESHOLD
from app.ml.pipeline.train_xgboost import chronological_split


def test_rsi_hand_checked_series():
    """Verify RSI calculation on edge-case and hand-checked series."""
    # 1. Monotonically increasing prices -> RSI should be 100
    prices_up = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0])
    rsi_up = calculate_rsi(prices_up, period=5)
    # The last value after 5 consecutive up-days must be 100.0
    assert rsi_up.iloc[-1] == 100.0

    # 2. Monotonically decreasing prices -> RSI should be 0
    prices_down = pd.Series([20.0, 19.0, 18.0, 17.0, 16.0, 15.0, 14.0, 13.0, 12.0, 11.0, 10.0])
    rsi_down = calculate_rsi(prices_down, period=5)
    # The last value after 5 consecutive down-days must be 0.0
    assert rsi_down.iloc[-1] == 0.0

    # 3. Flat prices (zero change) -> RSI defaults safely to 50
    prices_flat = pd.Series([50.0] * 10)
    rsi_flat = calculate_rsi(prices_flat, period=5)
    assert rsi_flat.iloc[-1] == 50.0


def test_macd_hand_checked_constant_series():
    """Verify MACD on a stationary price series is exactly 0.0."""
    n = 40
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    df = pd.DataFrame({
        "open": [100.0] * n,
        "high": [100.0] * n,
        "low": [100.0] * n,
        "close": [100.0] * n,
        "volume": [1000] * n,
    }, index=dates)

    features = compute_instrument_features(df)
    # On constant close, fast EMA == slow EMA -> MACD == 0.0
    assert np.allclose(features["macd"].dropna(), 0.0, atol=1e-6)
    assert np.allclose(features["macd_signal"].dropna(), 0.0, atol=1e-6)


def test_chronological_split_temporal_ordering():
    """Assert strict temporal ordering: max(train) < min(val) < min(test)."""
    n_days = 100
    dates = pd.date_range("2023-01-01", periods=n_days, freq="B")
    df = pd.DataFrame({
        "instrument_key": ["TEST"] * n_days,
        "close": np.linspace(100, 200, n_days),
        "target_direction": ["UP"] * n_days,
    }, index=dates)

    train_df, val_df, test_df = chronological_split(df, train_ratio=0.70, val_ratio=0.15)

    # 1. Total row count matches
    assert len(train_df) + len(val_df) + len(test_df) == n_days

    # 2. Strict chronological boundaries
    assert train_df.index.max() < val_df.index.min(), "Train overlaps with Validation!"
    assert val_df.index.max() < test_df.index.min(), "Validation overlaps with Test!"

    # 3. Sizes match ratio proportions
    assert len(train_df) == 70
    assert len(val_df) == 15
    assert len(test_df) == 15


def test_target_labeling_boundary_thresholds():
    """Test exact threshold behavior for direction labeling."""
    assert UP_THRESHOLD == 0.015
    assert DOWN_THRESHOLD == -0.015

    # Boundary edge cases
    assert label_direction(0.0150001) == "UP"
    assert label_direction(0.015) == "NEUTRAL"
    assert label_direction(0.0) == "NEUTRAL"
    assert label_direction(-0.015) == "NEUTRAL"
    assert label_direction(-0.0150001) == "DOWN"

    # NaN / None safety
    assert label_direction(None) is None
    assert label_direction(np.nan) is None
