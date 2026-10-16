"""
Unit and Integration Tests for FinPulse Codebase Alignment.

Tests:
1. YFinanceProvider: Symbol normalization, data retrieval, and error handling.
2. TechnicalAnalysisEngine: Precise calculations for SMA, EMA, RSI, and MACD including edge cases.
3. ProphetService: Input validation, forecast generation, confidence intervals, and holdout evaluation.
4. LSTMService: Sequence generation without leakage, model training, recursive multi-step forecasting, and MAE/RMSE metrics.
"""
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from app.services.market_data.yfinance_provider import YFinanceProvider, normalize_symbol_to_ticker
from app.services.technical_analysis import TechnicalAnalysisEngine
from app.ml.forecasting.prophet_service import ProphetService
from app.ml.forecasting.lstm_service import LSTMService, create_sequences


# ══════════════════════════════════════════════════════════════
# 1. Market Data Provider Tests
# ══════════════════════════════════════════════════════════════

class TestYFinanceProvider:
    def test_normalize_symbol(self):
        assert normalize_symbol_to_ticker("RELIANCE") == "RELIANCE.NS"
        assert normalize_symbol_to_ticker("TCS.NS") == "TCS.NS"
        assert normalize_symbol_to_ticker("AAPL") == "AAPL"
        assert normalize_symbol_to_ticker("^NSEI") == "^NSEI"
        assert normalize_symbol_to_ticker("NSE_EQ|INE002A01018") == "RELIANCE.NS"

    def test_invalid_symbol_handling(self):
        provider = YFinanceProvider()
        # Fetching a completely bogus ticker should return empty dataframe gracefully without exception
        df = provider.fetch_stock_dataframe("INVALID_BOGUS_TICKER_XYZ_999", period="5d")
        assert isinstance(df, pd.DataFrame)
        assert df.empty or len(df) == 0


# ══════════════════════════════════════════════════════════════
# 2. Technical Indicators Tests
# ══════════════════════════════════════════════════════════════

class TestTechnicalIndicators:
    def test_sma_calculation(self):
        prices = [10.0, 20.0, 30.0, 40.0, 50.0]
        # Period 3 SMA:
        # Index 0: None, Index 1: None
        # Index 2: (10+20+30)/3 = 20.0
        # Index 3: (20+30+40)/3 = 30.0
        # Index 4: (30+40+50)/3 = 40.0
        sma = TechnicalAnalysisEngine.calculate_sma(prices, 3)
        assert len(sma) == 5
        assert sma[0] is None
        assert sma[1] is None
        assert sma[2] == 20.0
        assert sma[3] == 30.0
        assert sma[4] == 40.0

    def test_sma_insufficient_data(self):
        prices = [10.0, 20.0]
        sma = TechnicalAnalysisEngine.calculate_sma(prices, 5)
        assert sma == [None, None]

    def test_ema_calculation(self):
        prices = [10.0, 10.0, 10.0, 10.0, 10.0]
        # Constant series EMA must equal price
        ema = TechnicalAnalysisEngine.calculate_ema(prices, 3)
        assert ema[0] is None
        assert ema[1] is None
        assert ema[2] == 10.0
        assert ema[3] == 10.0
        assert ema[4] == 10.0

    def test_ema_smoothing(self):
        prices = [10.0, 20.0, 30.0, 40.0]
        # Period 2 EMA:
        # k = 2 / (2 + 1) = 2/3 ≈ 0.6667
        # Index 0: None
        # Index 1: SMA(10, 20) = 15.0
        # Index 2: 30 * (2/3) + 15 * (1/3) = 20 + 5 = 25.0
        # Index 3: 40 * (2/3) + 25 * (1/3) = 26.6667 + 8.3333 = 35.0
        ema = TechnicalAnalysisEngine.calculate_ema(prices, 2)
        assert ema[0] is None
        assert ema[1] == 15.0
        assert abs(ema[2] - 25.0) < 0.01
        assert abs(ema[3] - 35.0) < 0.01

    def test_rsi_constant_series(self):
        # All flat prices -> no gain, no loss
        prices = [50.0] * 20
        rsi = TechnicalAnalysisEngine.calculate_rsi(prices, 14)
        assert len(rsi) == 20
        assert rsi[14] == 50.0

    def test_rsi_all_gains(self):
        # Strictly increasing prices -> RSI should be 100
        prices = [float(i) for i in range(1, 25)]
        rsi = TechnicalAnalysisEngine.calculate_rsi(prices, 14)
        valid_rsis = [r for r in rsi if r is not None]
        assert all(r == 100.0 for r in valid_rsis)

    def test_macd_structure(self):
        prices = [float(i + (i % 3)) for i in range(50)]
        res = TechnicalAnalysisEngine.calculate_macd(prices, fast=12, slow=26, signal=9)
        assert "macd" in res
        assert "signal" in res
        assert "histogram" in res
        assert len(res["macd"]) == len(prices)
        assert len(res["signal"]) == len(prices)
        assert len(res["histogram"]) == len(prices)
        # First 25 points must be None (insufficient lookback for slow=26)
        assert res["macd"][24] is None
        assert res["macd"][25] is not None

    def test_analyze_integration(self):
        candles = [
            {"timestamp": f"2026-01-{i+1:02d}", "open": 100.0, "high": 105.0, "low": 95.0, "close": 100.0 + i, "volume": 1000}
            for i in range(60)
        ]
        analyzed = TechnicalAnalysisEngine.analyze(candles)
        assert len(analyzed) == 60
        last = analyzed[-1]
        assert "sma_20" in last and last["sma_20"] is not None
        assert "sma_50" in last and last["sma_50"] is not None
        assert "ema_20" in last and last["ema_20"] is not None
        assert "ema_50" in last and last["ema_50"] is not None
        assert "rsi_14" in last and last["rsi_14"] is not None
        assert "macd" in last and last["macd"] is not None


# ══════════════════════════════════════════════════════════════
# 3. Prophet Forecasting Service Tests
# ══════════════════════════════════════════════════════════════

class TestProphetService:
    def test_prophet_insufficient_data(self):
        df = pd.DataFrame({
            "timestamp": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "close": [100.0, 102.0, 101.0],
        })
        res = ProphetService.forecast(df, horizon_days=5)
        assert res["status"] == "error"
        assert "Insufficient observations" in res["message"]

    def test_prophet_forecast_success(self):
        # Generate 60 days of upward synthetic price data
        base_date = datetime(2026, 1, 1)
        dates = [(base_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(60)]
        prices = [100.0 + i * 0.5 + np.sin(i / 3.0) for i in range(60)]
        df = pd.DataFrame({"timestamp": dates, "close": prices})

        res = ProphetService.forecast(df, horizon_days=7, evaluate_holdout=True)
        assert res["status"] == "success"
        assert res["model"] == "Facebook Prophet"
        assert res["horizon_days"] == 7
        assert len(res["forecast"]) == 7

        first_pt = res["forecast"][0]
        assert "date" in first_pt
        assert "predicted" in first_pt
        assert "lower" in first_pt
        assert "upper" in first_pt
        assert first_pt["lower"] <= first_pt["predicted"] <= first_pt["upper"]

        # Holdout metrics
        assert res["metrics"] is not None
        assert "mae" in res["metrics"]
        assert "rmse" in res["metrics"]
        assert res["metrics"]["mae"] >= 0.0
        assert res["metrics"]["rmse"] >= 0.0


# ══════════════════════════════════════════════════════════════
# 4. LSTM Forecasting Service Tests
# ══════════════════════════════════════════════════════════════

class TestLSTMService:
    def test_create_sequences_no_leakage(self):
        data = np.array([1, 2, 3, 4, 5, 6, 7])
        xs, ys = create_sequences(data, seq_length=3)
        # xs[0] = [1, 2, 3], ys[0] = 4
        # xs[1] = [2, 3, 4], ys[1] = 5
        # xs[2] = [3, 4, 5], ys[2] = 6
        # xs[3] = [4, 5, 6], ys[3] = 7
        assert len(xs) == 4
        assert np.array_equal(xs[0], [1, 2, 3])
        assert ys[0] == 4
        assert np.array_equal(xs[-1], [4, 5, 6])
        assert ys[-1] == 7

    def test_lstm_insufficient_data(self):
        df = pd.DataFrame({
            "timestamp": ["2026-01-01", "2026-01-02"],
            "close": [100.0, 101.0],
        })
        res = LSTMService.forecast(df, seq_length=15, horizon_days=5)
        assert res["status"] == "error"
        assert "Insufficient data" in res["message"]

    def test_lstm_forecast_success(self):
        # Generate 70 days of synthetic price data
        base_date = datetime(2026, 1, 1)
        dates = [(base_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(70)]
        prices = [150.0 + i * 0.4 + (i % 5) for i in range(70)]
        df = pd.DataFrame({"timestamp": dates, "close": prices})

        res = LSTMService.forecast(
            df,
            seq_length=10,
            horizon_days=5,
            epochs=5,
            batch_size=8,
        )
        assert res["status"] == "success"
        assert res["model"] in ["TensorFlow/Keras LSTM", "Recurrent Sequence Autoregressor (LSTM/Ridge)"]
        assert len(res["forecast"]) == 5
        assert "projected_price" in res
        assert "projected_change_percent" in res

        # Check metrics
        if res.get("metrics"):
            assert "mae" in res["metrics"]
            assert "rmse" in res["metrics"]
            assert res["metrics"]["mae"] >= 0.0
