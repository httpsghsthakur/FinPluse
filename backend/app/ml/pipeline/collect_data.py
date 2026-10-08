"""
Historical Market Data Ingestion Pipeline.

Supports:
1. Live ingestion from Upstox API using UPSTOX_ANALYTICS_TOKEN.
   - Normalises timestamps to midnight dates (removes time-of-day noise).
   - Ingests all 4 universe instruments.
   - Logs row counts and date ranges per instrument.
   - Fails loudly if credentials are missing or all fetches fail.
   - Saves strictly to data/raw/master_market_dataset.parquet.

2. Explicit synthetic sample generation via `--synthetic` flag.
   - Never saves synthetic data under real market data filenames.
   - Generates all 4 instruments with realistic starting levels and daily bars.
   - Saves to data/sample/synthetic_market_dataset.parquet.
   - Clearly logged as SYNTHETIC.
"""
from __future__ import annotations

import argparse
import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Tuple

import numpy as np
import pandas as pd
from app.core.logging import get_logger

logger = get_logger(__name__)

# Core universe (NIFTY 50 large-cap constituents)
UNIVERSE = [
    "NSE_EQ|INE002A01018",  # RELIANCE
    "NSE_EQ|INE040A01034",  # HDFCBANK
    "NSE_EQ|INE009A01021",  # INFY
    "NSE_EQ|INE467B01029",  # TCS
]

INSTRUMENT_NAMES = {
    "NSE_EQ|INE002A01018": "RELIANCE",
    "NSE_EQ|INE040A01034": "HDFCBANK",
    "NSE_EQ|INE009A01021": "INFY",
    "NSE_EQ|INE467B01029": "TCS",
}

PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_DIR = os.path.join(PIPELINE_DIR, "data", "raw")
SAMPLE_DATA_DIR = os.path.join(PIPELINE_DIR, "data", "sample")

REAL_OUTPUT_PATH = os.path.join(RAW_DATA_DIR, "master_market_dataset.parquet")
SYNTHETIC_OUTPUT_PATH = os.path.join(SAMPLE_DATA_DIR, "synthetic_market_dataset.parquet")


class DataCollector:
    """Ingests market data from Upstox or generates labeled synthetic samples."""

    def __init__(self, synthetic: bool = False, output_path: str | None = None):
        self.synthetic = synthetic
        self.output_path = output_path or (SYNTHETIC_OUTPUT_PATH if synthetic else REAL_OUTPUT_PATH)
        self.provider = None

        if not self.synthetic:
            token = os.environ.get("UPSTOX_ANALYTICS_TOKEN")
            if not token or not token.strip():
                raise ValueError(
                    "CRITICAL: UPSTOX_ANALYTICS_TOKEN environment variable is missing or empty. "
                    "Cannot collect real market data from Upstox API. "
                    "Set UPSTOX_ANALYTICS_TOKEN in your environment/backend/.env, "
                    "or pass '--synthetic' to generate a clearly labeled sample dataset."
                )
            # Lazy import to avoid unnecessary dependency if only synthetic is needed
            from app.services.market_data.upstox import UpstoxProvider
            self.provider = UpstoxProvider()

    async def fetch_history(self, instrument_key: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch historical daily candles for an instrument from Upstox and normalise."""
        if self.provider is None:
            raise RuntimeError("Provider not initialized.")

        candles = await self.provider.get_historical_candles(
            instrument_key=instrument_key,
            interval="1d",
            from_date=start_date,
            to_date=end_date,
        )
        if not candles:
            return pd.DataFrame()

        df = pd.DataFrame(candles)
        df["instrument_key"] = instrument_key

        # Normalise timestamp to date (midnight UTC/local) to eliminate time-of-day noise
        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize(None).dt.normalize()
        df.set_index("timestamp", inplace=True)
        df.sort_index(inplace=True)

        # Standardise columns
        required_cols = ["open", "high", "low", "close", "volume", "instrument_key"]
        available_cols = [c for c in required_cols if c in df.columns]
        return df[available_cols]

    def generate_synthetic_data(self, days_back: int = 2000, seed: int = 42) -> pd.DataFrame:
        """
        Generate explicitly labeled synthetic OHLCV data for all 4 universe instruments.
        
        Uses geometric random walk with realistic base prices and volatility parameters.
        All timestamps are normalised to pure calendar dates (no time-of-day noise).
        """
        logger.warning("=" * 70)
        logger.warning("GENERATING SYNTHETIC SAMPLE MARKET DATASET")
        logger.warning("CAUTION: This data is artificially simulated for testing/demo pipelines.")
        logger.warning("It must NEVER be represented as real market data.")
        logger.warning("=" * 70)

        rng = np.random.default_rng(seed)
        end_date = datetime.now().date()
        base_date = end_date - timedelta(days=days_back)

        # Realistic starting prices for the universe
        base_prices = {
            "NSE_EQ|INE002A01018": 2400.0,  # RELIANCE
            "NSE_EQ|INE040A01034": 1550.0,  # HDFCBANK
            "NSE_EQ|INE009A01021": 1450.0,  # INFY
            "NSE_EQ|INE467B01029": 3400.0,  # TCS
        }

        all_rows: List[dict] = []

        for instrument in UNIVERSE:
            price = base_prices.get(instrument, 1000.0)
            rows: List[dict] = []

            for i in range(days_back):
                cur_date = base_date + timedelta(days=i)
                # Skip weekends
                if cur_date.weekday() >= 5:
                    continue

                daily_ret = float(rng.normal(0.0003, 0.016))
                price = max(price * (1.0 + daily_ret), 10.0)

                intraday_vol = float(rng.uniform(0.008, 0.022))
                open_price = price * (1.0 + float(rng.normal(0, 0.004)))
                high_price = max(open_price, price) * (1.0 + intraday_vol * float(rng.uniform(0.4, 1.0)))
                low_price = min(open_price, price) * (1.0 - intraday_vol * float(rng.uniform(0.4, 1.0)))
                volume = int(rng.lognormal(mean=14.0, sigma=0.5))  # Realistic volume distribution

                rows.append({
                    "timestamp": pd.Timestamp(cur_date),
                    "instrument_key": instrument,
                    "open": round(open_price, 2),
                    "high": round(high_price, 2),
                    "low": round(low_price, 2),
                    "close": round(price, 2),
                    "volume": max(volume, 1000),
                })

            df_inst = pd.DataFrame(rows)
            sym = INSTRUMENT_NAMES.get(instrument, instrument)
            logger.info(
                f"[SYNTHETIC] Instrument {sym} ({instrument}): {len(df_inst)} rows, "
                f"range [{df_inst['timestamp'].min().strftime('%Y-%m-%d')} to "
                f"{df_inst['timestamp'].max().strftime('%Y-%m-%d')}]"
            )
            all_rows.extend(rows)

        full_df = pd.DataFrame(all_rows)
        full_df.set_index("timestamp", inplace=True)
        full_df.sort_index(inplace=True)
        return full_df

    async def run(self, days_back: int = 2000) -> pd.DataFrame:
        """Run collection pipeline."""
        if self.synthetic:
            master_df = self.generate_synthetic_data(days_back=days_back)
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            master_df.to_parquet(self.output_path, engine="pyarrow")
            logger.warning(
                f"Saved {len(master_df)} SYNTHETIC rows across {len(UNIVERSE)} instruments "
                f"to {self.output_path}"
            )
            return master_df

        # Real collection from Upstox
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        logger.info(f"Starting historical Upstox data collection: {start_str} to {end_str}")

        all_data: List[pd.DataFrame] = []
        failed_instruments: List[str] = []

        for instrument in UNIVERSE:
            sym = INSTRUMENT_NAMES.get(instrument, instrument)
            logger.info(f"Fetching real market data for {sym} ({instrument})...")
            try:
                df = await self.fetch_history(instrument, start_str, end_str)
                if not df.empty:
                    date_min = df.index.min().strftime('%Y-%m-%d')
                    date_max = df.index.max().strftime('%Y-%m-%d')
                    logger.info(
                        f"Instrument {sym} ({instrument}): {len(df)} rows collected, "
                        f"range [{date_min} to {date_max}]"
                    )
                    all_data.append(df)
                else:
                    logger.warning(f"No candles returned for {sym} ({instrument})")
                    failed_instruments.append(instrument)
            except Exception as e:
                logger.error(f"Failed to fetch {sym} ({instrument}): {e}")
                failed_instruments.append(instrument)

            await asyncio.sleep(0.5)

        if failed_instruments:
            logger.warning(
                f"Data collection incomplete: {len(failed_instruments)}/{len(UNIVERSE)} "
                f"instruments failed: {failed_instruments}"
            )

        if not all_data:
            raise RuntimeError(
                f"Failed to collect data for any instruments in universe. "
                f"All {len(UNIVERSE)} failed: {UNIVERSE}"
            )

        master_df = pd.concat(all_data)
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        master_df.to_parquet(self.output_path, engine="pyarrow")
        logger.info(
            f"Successfully saved {len(master_df)} real rows across "
            f"{len(all_data)}/{len(UNIVERSE)} instruments to {self.output_path}"
        )
        return master_df


def main():
    parser = argparse.ArgumentParser(description="Collect market data or generate labeled sample data.")
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="Generate synthetic sample market data labeled explicitly as SYNTHETIC in data/sample/.",
    )
    parser.add_argument(
        "--days-back",
        type=int,
        default=2000,
        help="Number of historical days to fetch or simulate (default: 2000).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Custom output parquet path.",
    )
    args = parser.parse_args()

    collector = DataCollector(synthetic=args.synthetic, output_path=args.output)
    asyncio.run(collector.run(days_back=args.days_back))


if __name__ == "__main__":
    main()
