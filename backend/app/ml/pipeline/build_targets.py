"""
FinPulse AI — Target Generation Pipeline.

Prediction Horizon & Target Specification:
------------------------------------------
- Timing: At row t, features summarize market state up to and including day t close.
- Target: 5-day forward return:
    future_return_5d = (Close_{t+5} - Close_t) / Close_t
- Directional Classes:
    UP:      future_return_5d > +0.015 (+1.5%)
    DOWN:    future_return_5d < -0.015 (-1.5%)
    NEUTRAL: -0.015 <= future_return_5d <= +0.015
- Forward Realized Volatility (5d):
    Annualized standard deviation of the next 5 forward daily returns:
    [return_1d_{t+1}, return_1d_{t+2}, ..., return_1d_{t+5}] * sqrt(252).
- Boundary Handling:
    The final 5 rows of each instrument series have undefined forward returns
    and are cleanly dropped.
"""
from __future__ import annotations

import argparse
import os
import numpy as np
import pandas as pd
from app.core.logging import get_logger

logger = get_logger(__name__)

PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
FEATURE_DATA_PATH = os.path.join(PIPELINE_DIR, "data", "processed", "features.parquet")
TARGET_DATA_PATH = os.path.join(PIPELINE_DIR, "data", "processed", "dataset_with_targets.parquet")

UP_THRESHOLD = 0.015    # +1.5% return over 5 trading days
DOWN_THRESHOLD = -0.015 # -1.5% return over 5 trading days


def label_direction(val: float | None) -> str | None:
    """Classify 5-day forward return into 3 discrete regimes."""
    if val is None or pd.isna(val):
        return None
    if val > UP_THRESHOLD:
        return "UP"
    elif val < DOWN_THRESHOLD:
        return "DOWN"
    return "NEUTRAL"


def compute_instrument_targets(group: pd.DataFrame) -> pd.DataFrame:
    """Compute forward targets for a single instrument's chronological series."""
    group = group.sort_index().copy()

    # 1. 5-day Forward Close and Return
    # shift(-5) pulls Close from 5 trading days into the future
    group['future_close_5d'] = group['close'].shift(-5)
    group['future_return_5d'] = (group['future_close_5d'] - group['close']) / group['close']

    # 2. Correct 5-day Forward Realized Volatility
    # Computes sample std over the forward 5 daily returns: [r_{t+1}, ..., r_{t+5}]
    forward_indexer = pd.api.indexers.FixedForwardWindowIndexer(window_size=5)
    group['future_volatility_5d'] = (
        group['return_1d'].shift(-1).rolling(window=forward_indexer).std() * np.sqrt(252)
    )

    # 3. Categorical Direction Target
    group['target_direction'] = group['future_return_5d'].apply(label_direction)

    # Drop the trailing 5 rows where future target is not yet observed
    group = group.dropna(subset=['target_direction'])
    return group


def build_targets(input_path: str | None = None, output_path: str | None = None) -> pd.DataFrame | None:
    """Generate forward targets from feature parquet."""
    src_path = input_path or FEATURE_DATA_PATH
    dst_path = output_path or TARGET_DATA_PATH

    if not os.path.exists(src_path):
        logger.error(f"Features file not found at {src_path}. Run build_features.py first.")
        return None

    df = pd.read_parquet(src_path)
    logger.info(f"Loaded {len(df)} rows. Generating forward targets...")

    processed_dfs = []
    for instrument, group in df.groupby('instrument_key'):
        inst_targets = compute_instrument_targets(group)
        processed_dfs.append(inst_targets)

    final_df = pd.concat(processed_dfs)

    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    final_df.to_parquet(dst_path, engine="pyarrow")

    dist = final_df['target_direction'].value_counts(normalize=True).to_dict()
    counts = final_df['target_direction'].value_counts().to_dict()
    logger.info(f"Target distribution counts: {counts}")
    logger.info(f"Target distribution proportions: {dist}")
    logger.info(f"Saved target dataset with shape {final_df.shape} to {dst_path}")
    return final_df


def main():
    parser = argparse.ArgumentParser(description="Generate forward return targets.")
    parser.add_argument("--input", type=str, default=None, help="Input features parquet path.")
    parser.add_argument("--output", type=str, default=None, help="Output target dataset parquet path.")
    args = parser.parse_args()

    build_targets(input_path=args.input, output_path=args.output)


if __name__ == "__main__":
    main()
