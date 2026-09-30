import os
import pandas as pd
import numpy as np
from app.core.logging import get_logger

logger = get_logger(__name__)

FEATURE_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "processed", "features.parquet")
STAGE2_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "processed", "features_stage2.parquet")

def build_sector_and_macro_features():
    """Generates Stage 2 Features: Sector momentum and fundamentals."""
    if not os.path.exists(FEATURE_DATA_PATH):
        logger.error("Stage 1 Features not found. Run build_features.py first.")
        return
        
    df = pd.read_parquet(FEATURE_DATA_PATH)
    logger.info(f"Loaded {len(df)} rows. Building Stage 2 features...")
    
    # Simulate adding NIFTY index data
    # In reality, this would join with the master dataset where symbol == NIFTY 50
    df['nifty_return_1d'] = df['return_1d'] + np.random.normal(0, 0.001, size=len(df))
    df['nifty_return_5d'] = df['return_5d'] + np.random.normal(0, 0.005, size=len(df))
    
    # Calculate Relative Momentum
    df['relative_momentum'] = df['return_20d'] - df['nifty_return_1d'].rolling(20).sum()
    
    # Mocking Fundamentals (Point-in-Time safe)
    # E.g., PE ratio is updated quarterly, carried forward
    df['pe_ratio'] = np.random.uniform(15, 30, size=len(df))
    df['roe'] = np.random.uniform(0.05, 0.25, size=len(df))
    
    # Market Breadth Proxy
    df['market_breadth_proxy'] = np.random.uniform(0.2, 0.8, size=len(df))
    
    df.to_parquet(STAGE2_DATA_PATH, engine="pyarrow")
    logger.info(f"Saved Stage 2 features with shape {df.shape} to {STAGE2_DATA_PATH}")

if __name__ == "__main__":
    build_sector_and_macro_features()
