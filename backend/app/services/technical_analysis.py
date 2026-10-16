"""
Technical Analysis Engine.

Calculates Simple Moving Average (SMA), Exponential Moving Average (EMA),
Relative Strength Index (RSI), and Moving Average Convergence Divergence (MACD)
from historical price time series.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np


class TechnicalAnalysisEngine:
    """Computes technical indicators for historical data with full edge-case safety."""

    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> List[Optional[float]]:
        """Calculate Simple Moving Average (SMA).
        
        Args:
            prices: Chronological list of price floats.
            period: Lookback window period (must be >= 1).
            
        Returns:
            List of SMA values matching input length, with None for insufficient lookback.
        """
        if not prices or period < 1:
            return []
        if len(prices) < period:
            return [None] * len(prices)

        sma: List[Optional[float]] = [None] * (period - 1)
        # Compute sliding sum
        window_sum = sum(prices[:period])
        sma.append(round(window_sum / period, 4))

        for i in range(period, len(prices)):
            window_sum += prices[i] - prices[i - period]
            sma.append(round(window_sum / period, 4))

        return sma

    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> List[Optional[float]]:
        """Calculate Exponential Moving Average (EMA).
        
        Uses initial SMA for seed value at index `period - 1`, then applies exponential smoothing multiplier.
        
        Args:
            prices: Chronological list of price floats.
            period: Lookback window period (must be >= 1).
            
        Returns:
            List of EMA values matching input length, with None for insufficient lookback.
        """
        if not prices or period < 1:
            return []
        if len(prices) < period:
            return [None] * len(prices)

        k = 2.0 / (period + 1.0)
        ema: List[Optional[float]] = [None] * (period - 1)

        # Seed with SMA of the first `period` observations
        initial_sma = sum(prices[:period]) / period
        ema.append(round(initial_sma, 4))

        current_ema = initial_sma
        for i in range(period, len(prices)):
            current_ema = (prices[i] * k) + (current_ema * (1.0 - k))
            ema.append(round(current_ema, 4))

        return ema

    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
        """Calculate Relative Strength Index (RSI) using Wilder's smoothing method.
        
        Args:
            prices: Chronological list of price floats.
            period: RSI period (default: 14).
            
        Returns:
            List of RSI values (0-100) matching input length, with None for insufficient lookback.
        """
        if not prices or period < 1:
            return []
        if len(prices) < period + 1:
            return [None] * len(prices)

        deltas = np.diff(prices)
        rsi: List[Optional[float]] = [None] * period

        # Initial average gain/loss
        seed = deltas[:period]
        gains = seed[seed > 0]
        losses = -seed[seed < 0]

        avg_gain = float(gains.sum() / period) if len(gains) > 0 else 0.0
        avg_loss = float(losses.sum() / period) if len(losses) > 0 else 0.0

        if avg_loss == 0.0:
            rsi.append(100.0 if avg_gain > 0 else 50.0)
        else:
            rs = avg_gain / avg_loss
            rsi.append(round(100.0 - (100.0 / (1.0 + rs)), 2))

        # Wilder's smoothing for subsequent steps
        for i in range(period, len(deltas)):
            delta = float(deltas[i])
            gain = delta if delta > 0 else 0.0
            loss = -delta if delta < 0 else 0.0

            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period

            if avg_loss == 0.0:
                current_rsi = 100.0 if avg_gain > 0 else 50.0
            else:
                rs = avg_gain / avg_loss
                current_rsi = 100.0 - (100.0 / (1.0 + rs))

            rsi.append(round(current_rsi, 2))

        return rsi

    @staticmethod
    def calculate_macd(
        prices: List[float],
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> Dict[str, List[Optional[float]]]:
        """Calculate Moving Average Convergence Divergence (MACD).
        
        Args:
            prices: Chronological list of price floats.
            fast: Fast EMA period (default: 12).
            slow: Slow EMA period (default: 26).
            signal: Signal line EMA period (default: 9).
            
        Returns:
            Dict containing 'macd', 'signal', and 'histogram' lists.
        """
        n = len(prices)
        if n < slow + signal:
            return {
                "macd": [None] * n,
                "signal": [None] * n,
                "histogram": [None] * n,
            }

        # Calculate fast and slow EMAs
        fast_ema = TechnicalAnalysisEngine.calculate_ema(prices, fast)
        slow_ema = TechnicalAnalysisEngine.calculate_ema(prices, slow)

        macd_line: List[Optional[float]] = []
        for f, s in zip(fast_ema, slow_ema):
            if f is not None and s is not None:
                macd_line.append(round(f - s, 4))
            else:
                macd_line.append(None)

        # Calculate signal line as EMA of the valid MACD line values
        valid_macd_indices = [i for i, val in enumerate(macd_line) if val is not None]
        valid_macd_values = [macd_line[i] for i in valid_macd_indices]  # type: ignore

        signal_valid = TechnicalAnalysisEngine.calculate_ema(valid_macd_values, signal)

        signal_line: List[Optional[float]] = [None] * n
        histogram: List[Optional[float]] = [None] * n

        for idx, sig_val in zip(valid_macd_indices, signal_valid):
            signal_line[idx] = sig_val
            m_val = macd_line[idx]
            if m_val is not None and sig_val is not None:
                histogram[idx] = round(m_val - sig_val, 4)

        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram,
        }

    @staticmethod
    def analyze(candles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add technical indicators (SMA, EMA, RSI, MACD) to a list of chronological candles."""
        if not candles:
            return []

        closes = [float(c["close"]) for c in candles]

        sma_20 = TechnicalAnalysisEngine.calculate_sma(closes, 20)
        sma_50 = TechnicalAnalysisEngine.calculate_sma(closes, 50)
        ema_20 = TechnicalAnalysisEngine.calculate_ema(closes, 20)
        ema_50 = TechnicalAnalysisEngine.calculate_ema(closes, 50)
        rsi_14 = TechnicalAnalysisEngine.calculate_rsi(closes, 14)
        macd_data = TechnicalAnalysisEngine.calculate_macd(closes, fast=12, slow=26, signal=9)

        for i, c in enumerate(candles):
            indicators_dict = {
                "sma_20": sma_20[i],
                "sma_50": sma_50[i],
                "ema_20": ema_20[i],
                "ema_50": ema_50[i],
                "rsi_14": rsi_14[i],
                "macd": macd_data["macd"][i],
                "macd_signal": macd_data["signal"][i],
                "macd_histogram": macd_data["histogram"][i],
            }
            c["indicators"] = indicators_dict
            # Top-level direct keys for chart ease
            c["sma_20"] = sma_20[i]
            c["sma_50"] = sma_50[i]
            c["ema_20"] = ema_20[i]
            c["ema_50"] = ema_50[i]
            c["rsi"] = rsi_14[i]
            c["rsi_14"] = rsi_14[i]
            c["macd"] = macd_data["macd"][i]
            c["macd_signal"] = macd_data["signal"][i]
            c["macd_histogram"] = macd_data["histogram"][i]

        return candles
