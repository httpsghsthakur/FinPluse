"""Market data provider abstraction."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

class MarketDataProvider(ABC):
    """Abstract base class for all market data providers."""
    
    @abstractmethod
    async def get_live_price(self, instrument_key: str) -> Optional[float]:
        """Get the latest live price for an instrument."""
        pass
        
    @abstractmethod
    async def get_historical_candles(self, instrument_key: str, interval: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """Get historical OHLCV candles."""
        pass
        
    @abstractmethod
    async def get_market_quote(self, instrument_key: str) -> Optional[Dict[str, Any]]:
        """Get full market quote including OHLC, volume, etc."""
        pass
        
    @abstractmethod
    async def search_instruments(self, query: str) -> List[Dict[str, Any]]:
        """Search for instruments by symbol or name."""
        pass
