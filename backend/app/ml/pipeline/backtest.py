import os
import pandas as pd
import numpy as np
from app.core.logging import get_logger
from app.ml.pipeline.predict import direction_predictor

logger = get_logger(__name__)

TARGET_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "processed", "dataset_with_targets.parquet")

def run_backtest(initial_capital: float = 100000.0, position_size: float = 0.1):
    """Leakage-free backtesting engine using the trained XGBoost model."""
    if not os.path.exists(TARGET_DATA_PATH):
        logger.error("Dataset not found. Run pipeline first.")
        return
        
    df = pd.read_parquet(TARGET_DATA_PATH)
    
    # Use only the test set (e.g. data >= 2024-01-01)
    split_date = pd.Timestamp("2024-01-01")
    test_df = df[df.index >= split_date].copy()
    
    if test_df.empty:
        logger.warning("No test data available for backtesting.")
        return
        
    logger.info(f"Starting backtest on {len(test_df)} observations...")
    
    capital = initial_capital
    portfolio_history = []
    
    for instrument, group in test_df.groupby('instrument_key'):
        group = group.sort_index()
        
        for idx, row in group.iterrows():
            # Extract features for prediction
            features = {f: row.get(f, 0.0) for f in direction_predictor.features}
            
            # This uses the strictly point-in-time model
            prediction = direction_predictor.predict(features)
            
            if prediction.get('status') == 'success':
                direction = prediction['direction']
                
                # Trading Logic (simplified for 5-day holding)
                if direction == 'UP':
                    # Simulate buying and holding for 5 days
                    # Using the actual future 5-day return from the dataset
                    trade_return = row['future_return_5d']
                    
                    # Transaction cost proxy (0.1% slippage + brokerage)
                    trade_return -= 0.001 
                    
                    profit = (capital * position_size) * trade_return
                    capital += profit
                    
            portfolio_history.append({'timestamp': idx, 'capital': capital})
            
    # Compile Results
    if portfolio_history:
        results_df = pd.DataFrame(portfolio_history).groupby('timestamp').last()
        total_return = (capital - initial_capital) / initial_capital
        
        logger.info("\n=== BACKTEST RESULTS ===")
        logger.info(f"Initial Capital: ₹{initial_capital:,.2f}")
        logger.info(f"Final Capital:   ₹{capital:,.2f}")
        logger.info(f"Total Return:    {total_return*100:.2f}%")
        logger.info("========================\n")
    else:
        logger.warning("Backtest yielded no trades.")

if __name__ == "__main__":
    run_backtest()
