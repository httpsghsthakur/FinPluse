"""
FinPulse AI — Vectorized Point-in-Time Backtesting Engine.

Methodology:
------------
1. In-Sample Free Testing:
   Runs strictly on the out-of-sample Test partition (last 15% chronological dates).
2. Vectorized Predictions:
   Generates model predictions across the entire test set simultaneously without row loops.
3. Realistic Position Management:
   Enforces non-overlapping 5-day holding periods per instrument to avoid fictitious
   compounding or multiple entries on the same price trajectory.
4. Transaction Friction:
   Accounts for brokerage and execution slippage as an explicit cost parameter.
5. Benchmark Comparison:
   Compares strategy performance against an equally weighted Buy-and-Hold portfolio.

DISCLAIMER:
-----------
Simulated, in-sample-free historical test, not trading advice.
"""
from __future__ import annotations

import argparse
import os
from typing import Dict, Any, List

import joblib
import numpy as np
import pandas as pd
from app.core.logging import get_logger

logger = get_logger(__name__)

PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_DATA_PATH = os.path.join(PIPELINE_DIR, "data", "processed", "dataset_with_targets.parquet")
MODEL_DIR = os.path.join(PIPELINE_DIR, "models")


def run_backtest(
    input_path: str | None = None,
    initial_capital: float = 100000.0,
    position_size: float = 0.25,
    transaction_cost: float = 0.001,  # 10 bps (0.10%) per trade slippage & brokerage
    test_ratio: float = 0.15,
) -> Dict[str, Any]:
    """Execute vectorized, non-overlapping backtest on test partition."""
    src_path = input_path or TARGET_DATA_PATH
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Dataset not found at {src_path}. Run build_targets.py first.")

    # Load artifacts
    clf = joblib.load(os.path.join(MODEL_DIR, "xgboost_direction.joblib"))
    le = joblib.load(os.path.join(MODEL_DIR, "label_encoder.joblib"))
    features = joblib.load(os.path.join(MODEL_DIR, "features.joblib"))

    df = pd.read_parquet(src_path)
    df = df.dropna(subset=features + ['target_direction', 'future_return_5d'])

    # Determine test cut date (last 15% of dates)
    unique_dates = np.array(sorted(df.index.unique()))
    test_start_idx = int(len(unique_dates) * (1.0 - test_ratio))
    test_start_date = unique_dates[test_start_idx]

    test_df = df[df.index >= test_start_date].copy()
    test_df.sort_index(inplace=True)

    if test_df.empty:
        raise ValueError(f"No test observations found after {test_start_date}.")

    logger.info(
        f"Starting vectorized backtest on {len(test_df)} test observations "
        f"across {test_df['instrument_key'].nunique()} instruments "
        f"[{test_df.index.min().strftime('%Y-%m-%d')} to {test_df.index.max().strftime('%Y-%m-%d')}]..."
    )

    # 1. VECTORIZED PREDICTION: Predict entire test set at once
    X_test = test_df[features]
    preds = clf.predict(X_test)
    test_df['pred_direction'] = le.inverse_transform(preds)

    # 2. Simulate Trades with NON-OVERLAPPING 5-day positions per instrument
    trades: List[Dict[str, Any]] = []
    capital = initial_capital
    capital_curve: List[Dict[str, Any]] = [{'timestamp': test_df.index.min(), 'capital': capital}]

    for instrument, group in test_df.groupby('instrument_key'):
        group = group.sort_index()
        n_rows = len(group)
        next_available_idx = 0

        for i in range(n_rows):
            if i < next_available_idx:
                # Instrument is locked in an active 5-day trade
                continue

            row = group.iloc[i]
            if row['pred_direction'] == 'UP':
                gross_ret = float(row['future_return_5d'])
                net_ret = gross_ret - transaction_cost  # deduct roundtrip slippage + fees
                allocated = capital * position_size
                pnl = allocated * net_ret

                trades.append({
                    "entry_date": group.index[i],
                    "exit_date": group.index[min(i + 5, n_rows - 1)],
                    "instrument": instrument,
                    "gross_return": gross_ret,
                    "net_return": net_ret,
                    "pnl": pnl,
                    "win": bool(net_ret > 0),
                })

                capital += pnl
                capital_curve.append({'timestamp': group.index[i], 'capital': capital})

                # Lock instrument for the 5-day holding period to prevent overlapping entries
                next_available_idx = i + 5

    # 3. Performance Metrics
    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t['win'])
    win_rate = (winning_trades / total_trades) if total_trades > 0 else 0.0
    total_return = (capital - initial_capital) / initial_capital

    # Max Drawdown calculation
    cap_df = pd.DataFrame(capital_curve).sort_values('timestamp').drop_duplicates('timestamp')
    cap_series = cap_df['capital']
    running_max = cap_series.cummax()
    drawdowns = (cap_series - running_max) / running_max
    max_drawdown = float(drawdowns.min()) if not drawdowns.empty else 0.0

    # 4. Buy-and-Hold Benchmark
    bah_returns = []
    for instrument, group in test_df.groupby('instrument_key'):
        group = group.sort_index()
        if len(group) >= 2:
            bah_ret = (group['close'].iloc[-1] - group['close'].iloc[0]) / group['close'].iloc[0]
            bah_returns.append(bah_ret)
    avg_bah_return = float(np.mean(bah_returns)) if bah_returns else 0.0

    # 5. Output Results with Disclaimer
    banner = (
        "\n" + "=" * 65 + "\n"
        "SIMULATED, IN-SAMPLE-FREE HISTORICAL TEST (NOT TRADING ADVICE)\n"
        + "=" * 65 + "\n"
        f"Test Period:             {test_df.index.min().strftime('%Y-%m-%d')} -> {test_df.index.max().strftime('%Y-%m-%d')}\n"
        f"Initial Capital:         INR {initial_capital:,.2f}\n"
        f"Final Capital:           INR {capital:,.2f}\n"
        f"Strategy Total Return:   {total_return * 100:+.2f}%\n"
        f"Buy & Hold Benchmark:    {avg_bah_return * 100:+.2f}%\n"
        f"Maximum Drawdown:        {max_drawdown * 100:.2f}%\n"
        f"Total Completed Trades:  {total_trades}\n"
        f"Win Rate:                {win_rate * 100:.1f}% ({winning_trades}/{total_trades})\n"
        f"Transaction Cost Proxy:  {transaction_cost * 100:.2f}% per trade\n"
        + "=" * 65 + "\n"
    )
    logger.info(banner)
    print(banner)

    return {
        "initial_capital": initial_capital,
        "final_capital": capital,
        "total_return": total_return,
        "benchmark_buy_and_hold_return": avg_bah_return,
        "max_drawdown": max_drawdown,
        "total_trades": total_trades,
        "win_rate": win_rate,
        "transaction_cost": transaction_cost,
    }


def main():
    parser = argparse.ArgumentParser(description="Run vectorized backtest on test dataset.")
    parser.add_argument("--input", type=str, default=None, help="Path to dataset_with_targets.parquet")
    parser.add_argument("--capital", type=float, default=100000.0, help="Initial capital in INR")
    parser.add_argument("--cost", type=float, default=0.001, help="Transaction cost / slippage fraction")
    args = parser.parse_args()

    run_backtest(input_path=args.input, initial_capital=args.capital, transaction_cost=args.cost)


if __name__ == "__main__":
    main()
