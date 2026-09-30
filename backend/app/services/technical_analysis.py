"""Technical Analysis Engine."""
from typing import List, Dict, Any, Optional
import numpy as np

class TechnicalAnalysisEngine:
    """Computes technical indicators for historical data."""

    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> List[Optional[float]]:
        """Calculate Simple Moving Average."""
        if len(prices) < period:
            return [None] * len(prices)
        
        sma = [None] * (period - 1)
        for i in range(period - 1, len(prices)):
            window = prices[i - period + 1 : i + 1]
            sma.append(sum(window) / period)
        return sma

    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
        """Calculate Relative Strength Index."""
        if len(prices) < period + 1:
            return [None] * len(prices)
            
        deltas = np.diff(prices)
        seed = deltas[:period]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        
        rs = up / down if down != 0 else 0
        rsi = np.zeros_like(prices, dtype=float)
        
        rsi[:period] = np.nan
        if down == 0:
            rsi[period] = 100.
        else:
            rsi[period] = 100. - 100. / (1. + rs)
            
        for i in range(period, len(prices) - 1):
            delta = deltas[i]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta
                
            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            
            rs = up / down if down != 0 else 0
            rsi[i + 1] = 100. - 100. / (1. + rs)
            
        result = []
        for val in rsi:
            if np.isnan(val):
                result.append(None)
            else:
                result.append(float(val))
        return result

    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, List[Optional[float]]]:
        """Calculate MACD."""
        if len(prices) < slow + signal:
            return {"macd": [None]*len(prices), "signal": [None]*len(prices), "histogram": [None]*len(prices)}
            
        def ema(data, period):
            k = 2 / (period + 1)
            ema_arr = np.zeros_like(data, dtype=float)
            ema_arr[0] = data[0]
            for i in range(1, len(data)):
                ema_arr[i] = data[i] * k + ema_arr[i-1] * (1 - k)
            return ema_arr
            
        prices_arr = np.array(prices)
        ema_fast = ema(prices_arr, fast)
        ema_slow = ema(prices_arr, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return {
            "macd": [float(x) for x in macd_line],
            "signal": [float(x) for x in signal_line],
            "histogram": [float(x) for x in histogram]
        }

    @staticmethod
    def analyze(candles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add technical indicators to a list of candles."""
        if not candles:
            return []
            
        closes = [c["close"] for c in candles]
        
        sma_20 = TechnicalAnalysisEngine.calculate_sma(closes, 20)
        sma_50 = TechnicalAnalysisEngine.calculate_sma(closes, 50)
        rsi_14 = TechnicalAnalysisEngine.calculate_rsi(closes, 14)
        macd_data = TechnicalAnalysisEngine.calculate_macd(closes)
        
        for i, c in enumerate(candles):
            c["indicators"] = {
                "sma_20": sma_20[i],
                "sma_50": sma_50[i],
                "rsi_14": rsi_14[i],
                "macd": macd_data["macd"][i],
                "macd_signal": macd_data["signal"][i],
                "macd_histogram": macd_data["histogram"][i]
            }
            
        return candles
