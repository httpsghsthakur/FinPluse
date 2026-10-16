"""
FinPulse — Predictive Financial Analytics Dashboard.

Streamlit interactive application supporting the workflow documented in the internship report:
Historical market data (yfinance) -> Preprocessing (Pandas/NumPy) -> Technical Indicators (SMA, EMA, RSI, MACD)
-> Forecasting Models (Prophet, TensorFlow/Keras LSTM) -> Interactive Dashboard with Matplotlib visualizations.
"""
import sys
import os
from datetime import datetime, timedelta

# Add backend directory to path so services can be directly imported
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from app.services.market_data.yfinance_provider import YFinanceProvider
from app.services.technical_analysis import TechnicalAnalysisEngine
from app.ml.forecasting.prophet_service import ProphetService
from app.ml.forecasting.lstm_service import LSTMService

# Page Configuration
st.set_page_config(
    page_title="FinPulse — Predictive Financial Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📈 FinPulse — Predictive Financial Analytics")
st.markdown(
    "**Workflow Pipeline:** Historical Data (`yfinance`) → Preprocessing (`Pandas/NumPy`) → "
    "Technical Indicators (`SMA, EMA, RSI, MACD`) → Forecasting (`Prophet, TensorFlow LSTM`) → Interactive Visualizations."
)

# ═══ Sidebar Controls ═══
st.sidebar.header("🕹️ Controls & Parameters")

universe_options = [
    "RELIANCE", "HDFCBANK", "INFY", "TCS", "ICICIBANK", "SBIN", "TATAMOTORS", "ITC", "AAPL", "MSFT"
]
selected_stock = st.sidebar.selectbox("Select Core Stock", universe_options, index=0)
custom_ticker = st.sidebar.text_input("Or Enter Custom Ticker", value="").strip().upper()
ticker = custom_ticker if custom_ticker else selected_stock

timeframe = st.sidebar.selectbox(
    "Historical Lookback Period",
    ["1mo", "3mo", "6mo", "1y", "2y"],
    index=3,
)

st.sidebar.subheader("Technical Overlays")
show_sma_20 = st.sidebar.checkbox("SMA (20-Day)", value=True)
show_sma_50 = st.sidebar.checkbox("SMA (50-Day)", value=True)
show_ema_20 = st.sidebar.checkbox("EMA (20-Day)", value=False)
show_ema_50 = st.sidebar.checkbox("EMA (50-Day)", value=False)
show_rsi = st.sidebar.checkbox("Show RSI (14-Day)", value=True)
show_macd = st.sidebar.checkbox("Show MACD (12, 26, 9)", value=True)

st.sidebar.subheader("Forecasting Models")
run_prophet = st.sidebar.checkbox("Run Facebook Prophet Forecast", value=True)
prophet_horizon = st.sidebar.slider("Prophet Horizon (Days)", min_value=7, max_value=60, value=30, step=7)

run_lstm = st.sidebar.checkbox("Run TensorFlow/Keras LSTM Forecast", value=True)
lstm_horizon = st.sidebar.slider("LSTM Horizon (Days)", min_value=5, max_value=30, value=14, step=1)
lstm_seq_len = st.sidebar.slider("LSTM Sequence Window (Days)", min_value=10, max_value=30, value=15, step=5)

# ═══ Data Acquisition & Processing ═══
yf_provider = YFinanceProvider()

with st.spinner(f"Fetching historical market data for {ticker}..."):
    df = yf_provider.fetch_stock_dataframe(ticker, period=timeframe)

if df.empty:
    st.error(f"Could not retrieve historical market data for ticker '{ticker}'. Please check the symbol and internet connection.")
    st.stop()

# Convert candles to dictionary list for indicator engine
candles = []
for _, row in df.iterrows():
    candles.append({
        "timestamp": str(row["timestamp"])[:10],
        "open": float(row["open"]),
        "high": float(row["high"]),
        "low": float(row["low"]),
        "close": float(row["close"]),
        "volume": float(row["volume"]),
    })

# Compute SMA, EMA, RSI, MACD
candles = TechnicalAnalysisEngine.analyze(candles)
processed_df = pd.DataFrame(candles)
processed_df["timestamp"] = pd.to_datetime(processed_df["timestamp"])

# ═══ Top Key Metrics ═══
last_row = processed_df.iloc[-1]
prev_row = processed_df.iloc[-2] if len(processed_df) > 1 else last_row
change = last_row["close"] - prev_row["close"]
change_pct = (change / prev_row["close"]) * 100 if prev_row["close"] != 0 else 0.0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Current Price", f"₹{last_row['close']:,.2f}", f"{change:+,.2f} ({change_pct:+.2f}%)")
col2.metric("Period High", f"₹{processed_df['high'].max():,.2f}")
col3.metric("Period Low", f"₹{processed_df['low'].min():,.2f}")
col4.metric("Observations", f"{len(processed_df)} Days")
rsi_curr = last_row.get("rsi")
col5.metric("RSI (14-Day)", f"{rsi_curr:.1f}" if rsi_curr else "N/A")

# ═══ Matplotlib Price & Indicators Chart ═══
st.subheader("📊 Historical Market Data & Technical Indicators")

fig, (ax_price, ax_vol) = plt.subplots(
    2, 1, figsize=(12, 6), sharex=True, gridspec_kw={"height_ratios": [3, 1]}
)
fig.patch.set_facecolor("#0e1117")
ax_price.set_facecolor("#161b22")
ax_vol.set_facecolor("#161b22")

# Price plot
ax_price.plot(processed_df["timestamp"], processed_df["close"], label="Close Price", color="#58a6ff", linewidth=1.8)

if show_sma_20 and "sma_20" in processed_df.columns:
    ax_price.plot(processed_df["timestamp"], processed_df["sma_20"], label="SMA 20", color="#d29922", linewidth=1.4)
if show_sma_50 and "sma_50" in processed_df.columns:
    ax_price.plot(processed_df["timestamp"], processed_df["sma_50"], label="SMA 50", color="#39c5cf", linewidth=1.4)
if show_ema_20 and "ema_20" in processed_df.columns:
    ax_price.plot(processed_df["timestamp"], processed_df["ema_20"], label="EMA 20", color="#bc8cff", linestyle="--", linewidth=1.4)
if show_ema_50 and "ema_50" in processed_df.columns:
    ax_price.plot(processed_df["timestamp"], processed_df["ema_50"], label="EMA 50", color="#3fb950", linestyle="--", linewidth=1.4)

ax_price.set_ylabel("Price (₹)", color="#c9d1d9")
ax_price.tick_params(colors="#8b949e")
ax_price.grid(True, linestyle=":", alpha=0.3, color="#8b949e")
ax_price.legend(loc="upper left", facecolor="#161b22", edgecolor="#30363d", labelcolor="#c9d1d9")

# Volume plot
ax_vol.bar(processed_df["timestamp"], processed_df["volume"], color="#58a6ff", alpha=0.5, width=0.8)
ax_vol.set_ylabel("Volume", color="#c9d1d9")
ax_vol.tick_params(colors="#8b949e")
ax_vol.grid(True, linestyle=":", alpha=0.3, color="#8b949e")
ax_vol.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))

st.pyplot(fig)

# ═══ RSI & MACD Sub-Charts ═══
col_rsi, col_macd = st.columns(2)

if show_rsi:
    with col_rsi:
        st.markdown("**Relative Strength Index (RSI 14)**")
        fig_rsi, ax_rsi = plt.subplots(figsize=(6, 2.8))
        fig_rsi.patch.set_facecolor("#0e1117")
        ax_rsi.set_facecolor("#161b22")
        ax_rsi.plot(processed_df["timestamp"], processed_df["rsi"], color="#3fb950", linewidth=1.5)
        ax_rsi.axhline(70, color="#d29922", linestyle="--", alpha=0.7, label="Overbought (70)")
        ax_rsi.axhline(30, color="#58a6ff", linestyle="--", alpha=0.7, label="Oversold (30)")
        ax_rsi.set_ylim(0, 100)
        ax_rsi.tick_params(colors="#8b949e")
        ax_rsi.grid(True, linestyle=":", alpha=0.3, color="#8b949e")
        ax_rsi.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        ax_rsi.legend(loc="lower left", facecolor="#161b22", edgecolor="#30363d", labelcolor="#c9d1d9", fontsize=8)
        st.pyplot(fig_rsi)

if show_macd:
    with col_macd:
        st.markdown("**MACD (12, 26, 9)**")
        fig_macd, ax_macd = plt.subplots(figsize=(6, 2.8))
        fig_macd.patch.set_facecolor("#0e1117")
        ax_macd.set_facecolor("#161b22")
        ax_macd.plot(processed_df["timestamp"], processed_df["macd"], color="#58a6ff", label="MACD", linewidth=1.4)
        ax_macd.plot(processed_df["timestamp"], processed_df["macd_signal"], color="#d29922", label="Signal", linewidth=1.4)
        
        hist = processed_df["macd_histogram"].fillna(0)
        colors = ["#3fb950" if h >= 0 else "#f85149" for h in hist]
        ax_macd.bar(processed_df["timestamp"], hist, color=colors, alpha=0.6, width=0.8, label="Histogram")
        ax_macd.tick_params(colors="#8b949e")
        ax_macd.grid(True, linestyle=":", alpha=0.3, color="#8b949e")
        ax_macd.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        ax_macd.legend(loc="lower left", facecolor="#161b22", edgecolor="#30363d", labelcolor="#c9d1d9", fontsize=8)
        st.pyplot(fig_macd)

# ═══ Machine Learning Forecasting Models ═══
st.markdown("---")
st.subheader("🔮 Machine Learning Forecasting Models")

tab_prophet, tab_lstm = st.tabs(["Facebook Prophet Model", "TensorFlow/Keras LSTM Model"])

with tab_prophet:
    if run_prophet:
        with st.spinner("Fitting Facebook Prophet model with chronological hold-out validation..."):
            prophet_res = ProphetService.forecast(df, horizon_days=prophet_horizon, evaluate_holdout=True)

        if prophet_res.get("status") == "success":
            p_metrics = prophet_res.get("metrics") or {}
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Projected Price", f"₹{prophet_res['projected_price']:,.2f}", f"{prophet_res['projected_change_percent']:+.2f}%")
            m2.metric("Horizon", f"{prophet_res['horizon_days']} Days")
            m3.metric("Test MAE", f"₹{p_metrics.get('mae', 'N/A')}")
            m4.metric("Test RMSE", f"₹{p_metrics.get('rmse', 'N/A')}")

            # Plot Prophet Forecast
            f_points = prophet_res["forecast"]
            f_df = pd.DataFrame(f_points)
            f_df["date"] = pd.to_datetime(f_df["date"])

            fig_p, ax_p = plt.subplots(figsize=(11, 4))
            fig_p.patch.set_facecolor("#0e1117")
            ax_p.set_facecolor("#161b22")

            # Historical close (last 60 days)
            recent_hist = processed_df.tail(60)
            ax_p.plot(recent_hist["timestamp"], recent_hist["close"], label="Historical Price", color="#58a6ff", linewidth=1.8)

            # Projected line
            # Connect last historical date to first forecast
            conn_dates = [recent_hist["timestamp"].iloc[-1]] + list(f_df["date"])
            conn_preds = [recent_hist["close"].iloc[-1]] + list(f_df["predicted"])
            ax_p.plot(conn_dates, conn_preds, label="Prophet Forecast", color="#bc8cff", linestyle="--", linewidth=2.0)

            # Confidence band
            ax_p.fill_between(f_df["date"], f_df["lower"], f_df["upper"], color="#bc8cff", alpha=0.18, label="80% Confidence Interval")

            ax_p.set_ylabel("Price (₹)", color="#c9d1d9")
            ax_p.tick_params(colors="#8b949e")
            ax_p.grid(True, linestyle=":", alpha=0.3, color="#8b949e")
            ax_p.legend(facecolor="#161b22", edgecolor="#30363d", labelcolor="#c9d1d9")
            ax_p.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
            st.pyplot(fig_p)
        else:
            st.warning(prophet_res.get("message", "Prophet forecasting could not be completed."))
    else:
        st.info("Enable 'Run Facebook Prophet Forecast' in the sidebar to generate time-series forecasts.")

with tab_lstm:
    if run_lstm:
        with st.spinner("Training TensorFlow/Keras LSTM on sliding sequence windows..."):
            lstm_res = LSTMService.forecast(
                df,
                seq_length=lstm_seq_len,
                horizon_days=lstm_horizon,
                epochs=20,
                batch_size=16,
            )

        if lstm_res.get("status") == "success":
            l_metrics = lstm_res.get("metrics") or {}
            l1, l2, l3, l4 = st.columns(4)
            l1.metric("Projected Price", f"₹{lstm_res['projected_price']:,.2f}", f"{lstm_res['projected_change_percent']:+.2f}%")
            l2.metric("Horizon", f"{lstm_res['horizon_days']} Days")
            l3.metric("Test MAE", f"₹{l_metrics.get('mae', 'N/A')}")
            l4.metric("Test RMSE", f"₹{l_metrics.get('rmse', 'N/A')}")

            # Plot LSTM Forecast
            f_points = lstm_res["forecast"]
            f_df = pd.DataFrame(f_points)
            f_df["date"] = pd.to_datetime(f_df["date"])

            fig_l, ax_l = plt.subplots(figsize=(11, 4))
            fig_l.patch.set_facecolor("#0e1117")
            ax_l.set_facecolor("#161b22")

            recent_hist = processed_df.tail(60)
            ax_l.plot(recent_hist["timestamp"], recent_hist["close"], label="Historical Price", color="#58a6ff", linewidth=1.8)

            conn_dates = [recent_hist["timestamp"].iloc[-1]] + list(f_df["date"])
            conn_preds = [recent_hist["close"].iloc[-1]] + list(f_df["predicted"])
            ax_l.plot(conn_dates, conn_preds, label="LSTM Recursive Forecast", color="#3fb950", linestyle="--", linewidth=2.0)

            ax_l.set_ylabel("Price (₹)", color="#c9d1d9")
            ax_l.tick_params(colors="#8b949e")
            ax_l.grid(True, linestyle=":", alpha=0.3, color="#8b949e")
            ax_l.legend(facecolor="#161b22", edgecolor="#30363d", labelcolor="#c9d1d9")
            ax_l.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
            st.pyplot(fig_l)
        else:
            st.warning(lstm_res.get("message", "LSTM forecasting could not be completed."))
    else:
        st.info("Enable 'Run TensorFlow/Keras LSTM Forecast' in the sidebar to generate sequential forecasts.")

st.markdown("---")
st.caption(
    "⚠️ **Disclaimer:** FinPulse forecasting models are experimental and designed for training & educational analytics. "
    "Predictions are based on mathematical models and do not guarantee future stock price performance."
)
