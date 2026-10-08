"""
FinPulse AI — End-to-End Pipeline Execution Script.

Runs the full 5-stage pipeline:
  1. Collect (or generate synthetic sample data)
  2. Build point-in-time features
  3. Build forward targets
  4. Train XGBoost classifier & baseline models
  5. Run vectorized out-of-sample backtest

Prints dataset shape and date range at each stage for complete auditability.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import pandas as pd

from app.ml.pipeline.collect_data import DataCollector, SAMPLE_DATA_DIR, RAW_DATA_DIR
from app.ml.pipeline.build_features import build_features, FEATURE_DATA_PATH
from app.ml.pipeline.build_targets import build_targets, TARGET_DATA_PATH
from app.ml.pipeline.train_xgboost import train_xgboost
from app.ml.pipeline.backtest import run_backtest

def print_dataset_info(stage_name: str, file_path: str):
    """Print dataset shape and date range for auditability."""
    if os.path.exists(file_path):
        df = pd.read_parquet(file_path)
        min_date = df.index.min().strftime('%Y-%m-%d') if hasattr(df.index, 'min') else 'N/A'
        max_date = df.index.max().strftime('%Y-%m-%d') if hasattr(df.index, 'max') else 'N/A'
        instruments = df['instrument_key'].nunique() if 'instrument_key' in df.columns else 'N/A'
        print(f"\n[{stage_name.upper()}] Output Audit:")
        print(f"  File:        {file_path}")
        print(f"  Shape:       {df.shape} ({len(df)} rows, {df.shape[1]} columns)")
        print(f"  Instruments: {instruments}")
        print(f"  Date Range:  {min_date} to {max_date}\n")
    else:
        print(f"\n[{stage_name.upper()}] Warning: Output file {file_path} not found.")

def run_pipeline(use_synthetic: bool = True):
    print("=" * 70)
    print("FINPULSE AI — EXECUTING REPRODUCIBLE ML PIPELINE")
    print(f"Mode: {'SYNTHETIC SAMPLE DATA' if use_synthetic else 'REAL UPSTOX INGESTION'}")
    print("=" * 70)

    # Stage 1: Collect Data
    print("\n>>> Stage 1/5: Collecting Market Data...")
    collector = DataCollector(synthetic=use_synthetic)
    asyncio.run(collector.run())
    print_dataset_info("Stage 1: Collect Data", collector.output_path)

    # Stage 2: Build Features
    print(">>> Stage 2/5: Building Point-in-Time Features...")
    build_features(input_path=collector.output_path)
    print_dataset_info("Stage 2: Features", FEATURE_DATA_PATH)

    # Stage 3: Build Targets
    print(">>> Stage 3/5: Generating Forward 5-Day Targets...")
    build_targets()
    print_dataset_info("Stage 3: Targets", TARGET_DATA_PATH)

    # Stage 4: Train XGBoost & Naive Baselines
    print(">>> Stage 4/5: Training XGBoost & Computing Baseline Comparisons...")
    metrics = train_xgboost()

    # Stage 5: Out-of-Sample Vectorized Backtest
    print(">>> Stage 5/5: Running Out-of-Sample Vectorized Backtest...")
    backtest_res = run_backtest()

    print("\n" + "=" * 70)
    print("END-TO-END PIPELINE RUN COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run full FinPulse ML pipeline.")
    parser.add_argument("--synthetic", action="store_true", default=True, help="Use synthetic sample data")
    parser.add_argument("--real", dest="synthetic", action="store_false", help="Use real Upstox market data")
    args = parser.parse_args()

    run_pipeline(use_synthetic=args.synthetic)
