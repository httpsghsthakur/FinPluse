"""
YFinance Market Data Provider.

Implements MarketDataProvider abstraction to retrieve real historical and quote
market data using yfinance for Indian (NSE/BSE) and Global equities.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import pandas as pd

from app.services.market_data.provider import MarketDataProvider

logger = logging.getLogger(__name__)


def normalize_symbol_to_ticker(symbol: str) -> str:
    """Normalize input symbol/instrument_key to yfinance ticker string."""
    cleaned = symbol.strip().upper()
    if "|" in cleaned:
        # e.g., NSE_EQ|INE002A01018 -> map known common ones, else fallback
        mapping = {
            "INE002A01018": "RELIANCE.NS",
            "INE040A01034": "HDFCBANK.NS",
            "INE009A01021": "INFY.NS",
            "INE467B01029": "TCS.NS",
            "INE090A01021": "ICICIBANK.NS",
            "INE062A01020": "SBIN.NS",
            "INE155A01022": "TATAMOTORS.NS",
            "INE154A01025": "ITC.NS",
        }
        isin = cleaned.split("|")[-1]
        if isin in mapping:
            return mapping[isin]
        return isin

    if cleaned.startswith("^"):
        return cleaned

    # Already has an exchange suffix like .NS, .BO, .L
    if "." in cleaned:
        return cleaned

    # Default Indian stock symbols to National Stock Exchange (.NS)
    # Global tickers (e.g., AAPL, MSFT, TSLA, NVDA) remain as-is
    global_equities = {"AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "TSLA", "NVDA", "SPY", "QQQ"}
    if cleaned in global_equities:
        return cleaned

    return f"{cleaned}.NS"


class YFinanceProvider(MarketDataProvider):
    """Retrieves live market quotes and historical candles via yfinance."""

    def __init__(self):
        import yfinance as yf
        self.yf = yf

    async def get_live_price(self, instrument_key: str) -> Optional[float]:
        """Fetch current LTP for symbol/ticker."""
        quote = await self.get_market_quote(instrument_key)
        if quote and "price" in quote:
            return float(quote["price"])
        return None

    async def get_historical_candles(
        self,
        instrument_key: str,
        interval: str = "1d",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        period: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve historical candles and format them chronologically."""
        df = self.fetch_stock_dataframe(
            instrument_key,
            start_date=from_date,
            end_date=to_date,
            period=period,
            interval=interval,
        )
        if df.empty:
            return []

        candles: List[Dict[str, Any]] = []
        for _, row in df.iterrows():
            ts_str = str(row["timestamp"])
            if len(ts_str) >= 10:
                ts_str = ts_str[:10]

            candles.append({
                "timestamp": ts_str,
                "open": round(float(row["open"]), 2),
                "high": round(float(row["high"]), 2),
                "low": round(float(row["low"]), 2),
                "close": round(float(row["close"]), 2),
                "volume": int(row["volume"]),
            })
        return candles

    async def get_market_quote(self, instrument_key: str) -> Optional[Dict[str, Any]]:
        """Fetch full quote for symbol."""
        ticker = normalize_symbol_to_ticker(instrument_key)
        try:
            t = self.yf.Ticker(ticker)
            hist = t.history(period="2d")
            if hist.empty:
                logger.warning(f"Empty history returned for quote on {ticker}")
                return None

            c_last = float(hist["Close"].iloc[-1])
            c_prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else c_last
            high = float(hist["High"].iloc[-1])
            low = float(hist["Low"].iloc[-1])
            volume = int(hist["Volume"].iloc[-1])
            change = c_last - c_prev
            pct = (change / c_prev) * 100 if c_prev != 0 else 0.0

            clean_sym = instrument_key.split("|")[-1].replace(".NS", "").replace(".BO", "")
            return {
                "symbol": clean_sym,
                "ticker": ticker,
                "price": round(c_last, 2),
                "ltp": round(c_last, 2),
                "change": round(change, 2),
                "change_percent": round(pct, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "volume": volume,
                "is_up": change >= 0,
            }
        except Exception as e:
            logger.error(f"Error fetching quote for {ticker}: {e}")
            return None

    async def search_instruments(self, query: str) -> List[Dict[str, Any]]:
        """Search instruments (returns common Indian and global tickers matching query)."""
        q = query.strip().upper()
        catalog = [
            {"symbol": "RELIANCE", "name": "Reliance Industries Limited", "exchange": "NSE"},
            {"symbol": "HDFCBANK", "name": "HDFC Bank Limited", "exchange": "NSE"},
            {"symbol": "INFY", "name": "Infosys Limited", "exchange": "NSE"},
            {"symbol": "TCS", "name": "Tata Consultancy Services", "exchange": "NSE"},
            {"symbol": "ICICIBANK", "name": "ICICI Bank Limited", "exchange": "NSE"},
            {"symbol": "SBIN", "name": "State Bank of India", "exchange": "NSE"},
            {"symbol": "TATAMOTORS", "name": "Tata Motors Limited", "exchange": "NSE"},
            {"symbol": "ITC", "name": "ITC Limited", "exchange": "NSE"},
            {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ"},
            {"symbol": "MSFT", "name": "Microsoft Corporation", "exchange": "NASDAQ"},
            {"symbol": "NVDA", "name": "NVIDIA Corporation", "exchange": "NASDAQ"},
        ]
        return [c for c in catalog if q in c["symbol"] or q in c["name"].upper()]

    def fetch_stock_dataframe(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[str] = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Fetch, clean, validate, and sort historical OHLCV DataFrame chronologically."""
        ticker = normalize_symbol_to_ticker(symbol)
        try:
            t = self.yf.Ticker(ticker)

            if start_date and end_date:
                # Add 1 day to end_date so yfinance includes the end_date
                try:
                    dt_end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                    end_param = dt_end.strftime("%Y-%m-%d")
                except Exception:
                    end_param = end_date
                df = t.history(start=start_date, end=end_param, interval=interval, auto_adjust=True)
            elif period:
                df = t.history(period=period, interval=interval, auto_adjust=True)
            else:
                df = t.history(period="1y", interval=interval, auto_adjust=True)

            if df is None or df.empty:
                logger.warning(f"No historical data found for {ticker}")
                return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

            df = df.reset_index()

            # Identify datetime column
            date_col = "Date" if "Date" in df.columns else ("Datetime" if "Datetime" in df.columns else df.columns[0])
            df["timestamp"] = pd.to_datetime(df[date_col]).dt.tz_localize(None).dt.strftime("%Y-%m-%d")

            # Standardize column names
            col_map = {
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
            for original, target in col_map.items():
                if original in df.columns:
                    df[target] = pd.to_numeric(df[original], errors="coerce")

            df = df.dropna(subset=["close", "open", "high", "low"])
            df = df.sort_values(by="timestamp").reset_index(drop=True)
            return df[["timestamp", "open", "high", "low", "close", "volume"]]

        except Exception as e:
            logger.error(f"Error fetching historical dataframe for {ticker}: {e}")
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
