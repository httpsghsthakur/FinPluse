"""
FinPulse AI — Feature Engineering Pipeline (Stage 1).

Prediction Timing Specification:
--------------------------------
- Timing Model: Features are computed at the close of trading day t using all historical
  data available up to and including day t close.
- Target Horizon: Predict the forward 5-day return from day t close to day t+5 close:
  Return_{t -> t+5} = (Close_{t+5} - Close_t) / Close_t.
- Leakage Prevention: No feature calculation accesses information after day t close.
  All rolling windows, momentum calculations, and EWMA filters look strictly backward (<= t).
- Note on Lag-Shift: Because features represent the state at day t close and targets represent
  the subsequent return over (t, t+5], an additional t-1 shift is NOT applied. Applying t-1
  would create an artificial 1-day stale information lag for an end-of-day prediction model.
"""
from __future__ import annotations

import argparse
import os
import numpy as np
import pandas as pd
from app.core.logging import get_logger

logger = get_logger(__name__)

PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_PATH = os.path.join(PIPELINE_DIR, "data", "raw", "master_market_dataset.parquet")
SAMPLE_DATA_PATH = os.path.join(PIPELINE_DIR, "data", "sample", "synthetic_market_dataset.parquet")
FEATURE_DATA_PATH = os.path.join(PIPELINE_DIR, "data", "processed", "features.parquet")


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Compute Relative Strength Index (RSI) using standard rolling window.
    Strictly backward-looking (<= t).
    """
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    
    # Handle division edge-cases
    rsi = rsi.where(avg_loss != 0, 100.0)
    rsi = rsi.where((avg_gain != 0) | (avg_loss != 0), 50.0)
    return rsi


def compute_instrument_features(group: pd.DataFrame) -> pd.DataFrame:
    """
    Compute point-in-time technical and statistical features for a single instrument.
    Guaranteed: No feature depends on any row > t.
    """
    group = group.sort_index().copy()

    # 1. Price-Derived Returns (strictly backward-looking)
    group['return_1d'] = group['close'].pct_change()
    group['return_5d'] = group['close'].pct_change(5)
    group['return_20d'] = group['close'].pct_change(20)

    # 2. Historical Realized Volatility (rolling 20-day annualized)
    group['volatility_20d'] = group['return_1d'].rolling(20, min_periods=20).std() * np.sqrt(252)

    # 3. Moving Averages
    group['sma_20'] = group['close'].rolling(20, min_periods=20).mean()
    group['sma_50'] = group['close'].rolling(50, min_periods=50).mean()
    group['sma_200'] = group['close'].rolling(200, min_periods=200).mean()

    # 4. Momentum & Oscillators
    group['rsi_14'] = calculate_rsi(group['close'], period=14)

    # MACD (12, 26, 9)
    exp1 = group['close'].ewm(span=12, adjust=False).mean()
    exp2 = group['close'].ewm(span=26, adjust=False).mean()
    group['macd'] = exp1 - exp2
    group['macd_signal'] = group['macd'].ewm(span=9, adjust=False).mean()

    # Bollinger Bands (20-day, 2 std)
    rolling_std = group['close'].rolling(20, min_periods=20).std()
    group['bollinger_upper'] = group['sma_20'] + (rolling_std * 2)
    group['bollinger_lower'] = group['sma_20'] - (rolling_std * 2)

    # 5. Volume Features
    group['volume_ma_20'] = group['volume'].rolling(20, min_periods=20).mean()
    group['relative_volume'] = group['volume'] / group['volume_ma_20'].replace(0, np.nan)

    return group


def build_features(input_path: str | None = None, output_path: str | None = None) -> pd.DataFrame | None:
    """
    Generate point-in-time features for all instruments.
    Loads real raw data if available, or falls back to synthetic sample data with warning.
    """
    target_output = output_path or FEATURE_DATA_PATH

    # Determine input path
    source_path = input_path or os.environ.get("MARKET_DATA_PATH")
    if source_path is None:
        if os.path.exists(RAW_DATA_PATH):
            source_path = RAW_DATA_PATH
            logger.info(f"Loading real market data from {RAW_DATA_PATH}")
        elif os.path.exists(SAMPLE_DATA_PATH):
            source_path = SAMPLE_DATA_PATH
            logger.warning(
                f"Raw market data not found at {RAW_DATA_PATH}. "
                f"Falling back to SYNTHETIC sample dataset at {SAMPLE_DATA_PATH}. "
                f"All downstream metrics reflect simulated behavior!"
            )
        else:
            logger.error(
                f"No input data found! Looked for real data at {RAW_DATA_PATH} "
                f"and synthetic sample at {SAMPLE_DATA_PATH}. Run collect_data.py first."
            )
            return None
    else:
        logger.info(f"Loading market data from explicit path: {source_path}")

    df = pd.read_parquet(source_path)
    logger.info(f"Loaded {len(df)} rows across {df['instrument_key'].nunique()} instruments.")

    processed_dfs = []
    for instrument, group in df.groupby('instrument_key'):
        feat_df = compute_instrument_features(group)
        processed_dfs.append(feat_df)

    final_df = pd.concat(processed_dfs)

    os.makedirs(os.path.dirname(target_output), exist_ok=True)
    final_df.to_parquet(target_output, engine="pyarrow")
    logger.info(f"Saved feature dataset with shape {final_df.shape} to {target_output}")
    return final_df


def main():
    parser = argparse.ArgumentParser(description="Build point-in-time technical features.")
    parser.add_argument("--input", type=str, default=None, help="Input raw or sample parquet path.")
    parser.add_argument("--output", type=str, default=None, help="Output features parquet path.")
    args = parser.parse_args()

    build_features(input_path=args.input, output_path=args.output)


if __name__ == "__main__":
    main()
