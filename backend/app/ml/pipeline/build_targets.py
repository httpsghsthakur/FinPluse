import os
import pandas as pd
from app.core.logging import get_logger

logger = get_logger(__name__)

FEATURE_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "processed", "features.parquet")
TARGET_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "processed", "dataset_with_targets.parquet")

UP_THRESHOLD = 0.015   # 1.5% return over 5 days
DOWN_THRESHOLD = -0.015 # -1.5% return over 5 days

def label_direction(val: float) -> str:
    if pd.isna(val):
        return None
    if val > UP_THRESHOLD:
        return "UP"
    elif val < DOWN_THRESHOLD:
        return "DOWN"
    return "NEUTRAL"

def build_targets():
    """Generates the future targets. Future data strictly used ONLY for targets, not features."""
    if not os.path.exists(FEATURE_DATA_PATH):
        logger.error("Features not found. Run build_features.py first.")
        return
        
    df = pd.read_parquet(FEATURE_DATA_PATH)
    logger.info(f"Loaded {len(df)} rows. Building targets...")
    
    processed_dfs = []
    
    for instrument, group in df.groupby('instrument_key'):
        group = group.sort_index()
        
        # Calculate future 5-day return
        # Shift(-5) pulls the price from 5 days in the future to the current row
        group['future_close_5d'] = group['close'].shift(-5)
        group['future_return_5d'] = (group['future_close_5d'] - group['close']) / group['close']
        
        # Calculate future realized volatility (5d)
        future_returns = group['return_1d'].shift(-5).rolling(5).std() * np.sqrt(252) # approximation
        group['future_volatility_5d'] = future_returns
        
        # Assign categorical direction
        group['target_direction'] = group['future_return_5d'].apply(label_direction)
        
        # Drop rows where target is NaN (the last 5 days of the dataset)
        group = group.dropna(subset=['target_direction'])
        
        processed_dfs.append(group)
        
    final_df = pd.concat(processed_dfs)
    
    final_df.to_parquet(TARGET_DATA_PATH, engine="pyarrow")
    logger.info(f"Target distribution:\n{final_df['target_direction'].value_counts(normalize=True)}")
    logger.info(f"Saved target dataset with shape {final_df.shape} to {TARGET_DATA_PATH}")

if __name__ == "__main__":
    import numpy as np # Local import for volatility approx
    build_targets()
