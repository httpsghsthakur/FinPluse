"""Upstox Market Data Provider implementation."""
import os
import httpx
from typing import List, Dict, Any, Optional

from app.services.market_data.provider import MarketDataProvider
from app.core.logging import get_logger

logger = get_logger(__name__)

class UpstoxProvider(MarketDataProvider):
    """Upstox Analytics API implementation for market data."""
    
    def __init__(self):
        self.base_url = "https://api.upstox.com/v2"
        self.token = os.environ.get("UPSTOX_ANALYTICS_TOKEN")
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        
    async def get_live_price(self, instrument_key: str) -> Optional[float]:
        """Fetch live price using Upstox market quote API."""
        quote = await self.get_market_quote(instrument_key)
        if quote and "last_price" in quote:
            return float(quote["last_price"])
        return None

    async def get_market_quote(self, instrument_key: str) -> Optional[Dict[str, Any]]:
        """Fetch full market quote."""
        if not self.token:
            logger.warning("Upstox Analytics Token is missing.")
            return None
            
        url = f"{self.base_url}/market-quote/quotes"
        params = {"instrument_key": instrument_key}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success" and data.get("data"):
                        return data["data"].get(instrument_key)
                return None
        except Exception as e:
            logger.error(f"Error fetching Upstox market quote: {e}")
            return None

    async def get_historical_candles(self, instrument_key: str, interval: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """Fetch historical candles."""
        if not self.token:
            logger.warning("Upstox Analytics Token is missing.")
            return []
            
        url = f"{self.base_url}/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success" and data.get("data"):
                        candles = data["data"].get("candles", [])
                        return [
                            {
                                "timestamp": c[0],
                                "open": float(c[1]),
                                "high": float(c[2]),
                                "low": float(c[3]),
                                "close": float(c[4]),
                                "volume": float(c[5])
                            }
                            for c in candles
                        ]
                return []
        except Exception as e:
            logger.error(f"Error fetching Upstox historical candles: {e}")
            return []

    async def search_instruments(self, query: str) -> List[Dict[str, Any]]:
        """Upstox does not provide a direct search API in the free tier, 
        typically requires downloading the instrument master file."""
        # For now, returning empty list as placeholder. Real implementation 
        # would download https://assets.upstox.com/ts/instruments/instruments.csv.gz
        # and search it locally in the DB.
        return []
