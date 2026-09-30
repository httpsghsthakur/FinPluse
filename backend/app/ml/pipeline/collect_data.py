import os
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import List
from app.services.market_data.upstox import UpstoxProvider
from app.core.logging import get_logger

logger = get_logger(__name__)

# Core universe (NIFTY 50 example constituents)
UNIVERSE = [
    "NSE_EQ|INE002A01018", # RELIANCE
    "NSE_EQ|INE040A01034", # HDFCBANK
    "NSE_EQ|INE009A01021", # INFY
    "NSE_EQ|INE467B01029", # TCS
]

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "raw")

class DataCollector:
    def __init__(self):
        self.provider = UpstoxProvider()
        os.makedirs(DATA_DIR, exist_ok=True)

    async def fetch_history(self, instrument_key: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch historical daily data for a specific instrument."""
        candles = await self.provider.get_historical_candles(
            instrument_key=instrument_key,
            interval="1d",
            from_date=start_date,
            to_date=end_date
        )
        if not candles:
            return pd.DataFrame()
        
        df = pd.DataFrame(candles)
        df['instrument_key'] = instrument_key
        # Convert timestamp which might be isoformat from Upstox
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        return df

    async def run(self, days_back: int = 2000):
        """Run the collection pipeline for the defined universe."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        logger.info(f"Starting historical data collection from {start_str} to {end_str}")
        
        all_data = []
        for instrument in UNIVERSE:
            logger.info(f"Fetching data for {instrument}...")
            df = await self.fetch_history(instrument, start_str, end_str)
            if not df.empty:
                all_data.append(df)
            # Sleep to respect rate limits
            await asyncio.sleep(0.5)
            
        if all_data:
            master_df = pd.concat(all_data)
            output_path = os.path.join(DATA_DIR, "master_market_dataset.parquet")
            
            # If exists, incremental update logic goes here. For simplicity, overwriting.
            master_df.to_parquet(output_path, engine="pyarrow")
            logger.info(f"Saved {len(master_df)} rows to {output_path}")
        else:
            logger.warning("No data collected.")

if __name__ == "__main__":
    collector = DataCollector()
    asyncio.run(collector.run())
