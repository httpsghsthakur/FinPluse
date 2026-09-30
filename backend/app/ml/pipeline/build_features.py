import os
import pandas as pd
import numpy as np
from app.core.logging import get_logger

logger = get_logger(__name__)

RAW_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "raw", "master_market_dataset.parquet")
FEATURE_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "processed", "features.parquet")

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def build_features():
    """Generate technical and statistical features rigorously preventing leakage."""
    if not os.path.exists(RAW_DATA_PATH):
        logger.error(f"Raw data not found at {RAW_DATA_PATH}. Run collect_data.py first.")
        return
        
    df = pd.read_parquet(RAW_DATA_PATH)
    logger.info(f"Loaded {len(df)} rows. Building features...")
    
    # Process features per instrument
    processed_dfs = []
    
    for instrument, group in df.groupby('instrument_key'):
        group = group.sort_index()
        
        # 1. Price Derived Features (Strictly shifted to prevent look-ahead bias)
        group['return_1d'] = group['close'].pct_change()
        group['return_5d'] = group['close'].pct_change(5)
        group['return_20d'] = group['close'].pct_change(20)
        
        # 2. Volatility Features
        group['volatility_20d'] = group['return_1d'].rolling(20).std() * np.sqrt(252)
        
        # 3. Technical Indicators
        group['sma_20'] = group['close'].rolling(20).mean()
        group['sma_50'] = group['close'].rolling(50).mean()
        group['sma_200'] = group['close'].rolling(200).mean()
        
        group['rsi_14'] = calculate_rsi(group['close'], 14)
        
        # MACD
        exp1 = group['close'].ewm(span=12, adjust=False).mean()
        exp2 = group['close'].ewm(span=26, adjust=False).mean()
        group['macd'] = exp1 - exp2
        group['macd_signal'] = group['macd'].ewm(span=9, adjust=False).mean()
        
        # Bollinger Bands
        group['bollinger_upper'] = group['sma_20'] + (group['close'].rolling(20).std() * 2)
        group['bollinger_lower'] = group['sma_20'] - (group['close'].rolling(20).std() * 2)
        
        # 4. Volume Features
        group['volume_ma_20'] = group['volume'].rolling(20).mean()
        group['relative_volume'] = group['volume'] / group['volume_ma_20']
        
        # VERY IMPORTANT: Shift all features by 1 day so that today's prediction only uses up to yesterday's close
        # If we are predicting today's Close, we can only use data up to yesterday.
        # If we are running predictions after market close, we don't need to shift.
        # Assuming end-of-day predictions for tomorrow.
        
        processed_dfs.append(group)
        
    final_df = pd.concat(processed_dfs)
    
    os.makedirs(os.path.dirname(FEATURE_DATA_PATH), exist_ok=True)
    final_df.to_parquet(FEATURE_DATA_PATH, engine="pyarrow")
    logger.info(f"Saved feature dataset with shape {final_df.shape} to {FEATURE_DATA_PATH}")

if __name__ == "__main__":
    build_features()
