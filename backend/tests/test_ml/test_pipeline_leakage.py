"""
Unit tests asserting strict point-in-time calculation with zero future leakage.
"""
import numpy as np
import pandas as pd
import pytest

from app.ml.pipeline.build_features import compute_instrument_features, calculate_rsi
from app.ml.pipeline.build_targets import label_direction, UP_THRESHOLD, DOWN_THRESHOLD


def test_no_future_leakage_in_features():
    """
    Assert that features at row t are strictly invariant to any future rows (> t) being altered.
    
    If any feature formula looks forward in time, modifying future prices/volumes
    will alter row t's feature values, failing this assertion.
    """
    n_rows = 100
    dates = pd.date_range("2023-01-01", periods=n_rows, freq="B")
    
    rng = np.random.default_rng(123)
    base_prices = 1000.0 * np.cumprod(1.0 + rng.normal(0.0005, 0.015, size=n_rows))
    volumes = rng.integers(50000, 200000, size=n_rows)
    
    df_original = pd.DataFrame({
        "instrument_key": ["TEST_STOCK"] * n_rows,
        "open": base_prices * 0.99,
        "high": base_prices * 1.02,
        "low": base_prices * 0.98,
        "close": base_prices,
        "volume": volumes,
    }, index=dates)
    
    # Target row t (e.g. index 60, well after warm-up periods for 20/50 day rolling windows)
    t = 60
    
    # 1. Compute features on original data
    features_orig = compute_instrument_features(df_original)
    row_t_orig = features_orig.iloc[t].copy()
    
    # 2. Create modified DataFrame where all future rows (t+1 through end) are radically altered
    df_altered = df_original.copy()
    # Heavily corrupt future prices and volumes
    df_altered.iloc[t + 1:, df_altered.columns.get_loc("close")] = 999999.0
    df_altered.iloc[t + 1:, df_altered.columns.get_loc("open")] = 999999.0
    df_altered.iloc[t + 1:, df_altered.columns.get_loc("high")] = 999999.0
    df_altered.iloc[t + 1:, df_altered.columns.get_loc("low")] = 1.0
    df_altered.iloc[t + 1:, df_altered.columns.get_loc("volume")] = 1
    
    # 3. Compute features on altered future data
    features_altered = compute_instrument_features(df_altered)
    row_t_altered = features_altered.iloc[t].copy()
    
    # Feature columns to check
    feature_cols = [
        "return_1d", "return_5d", "return_20d",
        "volatility_20d", "sma_20", "sma_50",
        "rsi_14", "macd", "macd_signal",
        "bollinger_upper", "bollinger_lower",
        "volume_ma_20", "relative_volume"
    ]
    
    for col in feature_cols:
        val_orig = row_t_orig[col]
        val_alt = row_t_altered[col]
        assert np.isclose(val_orig, val_alt, rtol=1e-7, atol=1e-7, equal_nan=True), (
            f"LEAKAGE DETECTED in feature '{col}' at index {t}! "
            f"Original: {val_orig}, Altered: {val_alt}"
        )


def test_target_labeling_thresholds():
    """Verify target directional labeling thresholds."""
    assert label_direction(0.02) == "UP"
    assert label_direction(0.0151) == "UP"
    assert label_direction(-0.02) == "DOWN"
    assert label_direction(-0.0151) == "DOWN"
    assert label_direction(0.01) == "NEUTRAL"
    assert label_direction(-0.01) == "NEUTRAL"
    assert label_direction(0.0) == "NEUTRAL"
    assert label_direction(None) is None
    assert label_direction(np.nan) is None
