# FinPulse AI — Market Intelligence & Financial Copilot

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19.0-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![XGBoost](https://img.shields.io/badge/XGBoost-2.1-blue?style=for-the-badge)
![Prophet](https://img.shields.io/badge/Prophet-1.1%2B-red?style=for-the-badge)
![yfinance](https://img.shields.io/badge/Live_Data-yfinance_%26_Upstox-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Project-Production_Ready_Full_Stack-emerald?style=for-the-badge)

**An institutional-grade quantitative finance and personal financial copilot platform combining live external market ingestion, point-in-time machine learning, deep time-series forecasting, walk-forward backtesting, and grounded AI financial reasoning.**

</div>

---

## Academic & Engineering Integrity Statement

> [!NOTE]
> This platform prioritizes empirical rigor, zero lookahead leakage, and reproducibility over black-box claims:
> - **Zero Lookahead Leakage**: All technical indicators and predictive features are computed strictly on historical observations available up to day $t$ close ($15:30$ IST) to project directional outcomes from $t$ to $t+5$.
> - **Untouched Test Partition**: Model evaluation and metrics are measured on an out-of-sample test partition (the final 15% of historical chronological dates).
> - **Benchmarking Against Naive Baselines**: Machine learning models are benchmarked directly against random chance, always-majority class, and 5-day momentum persistence heuristics.
> - **Tool-First Determinism**: The AI Copilot computes net worth, runway, cash flow cushions, and budget thresholds using deterministic Python financial algorithms rather than allowing LLMs to hallucinate arithmetic.
> - **Multi-Source Market Ingestion**: Leverages Yahoo Finance (`yfinance`) with fallback to the Upstox API and local Parquet data lakes, ensuring continuous market telemetry.

---

## High-Level System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       FinPulse AI Distributed Architecture                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                       ┌───────────────┴───────────────┐
                       ▼                               ▼
             React 19 + TypeScript             FastAPI Application
               (Vite, Tailwind v4)              (Async ASGI Engine)
                       │                               │
                       │          REST API & SSE       │
                       └───────────────┬───────────────┘
                                       ▼
       ┌───────────────────────────────────────────────────────────────┐
       │                  Core Intelligence Subsystems                 │
       ├───────────────────────────────┬───────────────────────────────┤
       │ • Live Multi-Market Ingestion │ • Deep Forecasting Engines    │
       │   - yfinance (NSE, BSE, US)   │   - Facebook Prophet          │
       │   - Upstox Fallback           │   - Dual-Engine LSTM / Recurr │
       │   - 6 Thematic Sector Heatmaps│ • AI Financial Copilot        │
       │ • XGBoost Directional Model   │   - Semantic Item Pricing     │
       │   - 13 Point-in-Time Features │   - Grounded Runway Analysis  │
       │   - Vectorized Walk-Forward   │   - Offline Reasoning Engine  │
       └───────────────────────────────┴───────────────────────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │   Data & Persistence Layer    │
                       ├───────────────────────────────┤
                       │ • PostgreSQL (Production) /   │
                       │   SQLite via aiosqlite (Dev)  │
                       │ • Apache Parquet Data Lakes   │
                       │ • Serialized Models (JSON/Job)│
                       └───────────────────────────────┘
```

---

## Key Platform Features

### 1. Live Multi-Market Ingestion & Thematic Heatmaps
- **Dual Ingestion Providers**: `YFinanceProvider` and `UpstoxProvider` deliver real-time OHLCV candles, day highs/lows, LTP, and volume.
- **Automated Ticker Normalization**: Transparently handles Indian ISIN keys (`NSE_EQ|INE002A01018` $\rightarrow$ `RELIANCE.NS`), benchmark indices (`^NSEI`, `^NSEBANK`, `^BSESN`, `^INDIAVIX`), and global markets (`^GSPC`, `^IXIC`, `AAPL`, `MSFT`, `NVDA`).
- **NSE Sectoral Heatmap**: Live tracking of 6 core Indian thematic sectors (Technology, Financials, Energy, Auto, FMCG, Healthcare).
- **Float Sanitization (`_safe_float`)**: Eliminates JSON serialization crashes by filtering out IEEE 754 `NaN` or `Infinity` values during off-hours or trading halts.

### 2. Quantitative Directional Forecasting (XGBoost 3-Class)
- **13 Point-in-Time Features**: SMA (20, 50, 200), RSI (14), MACD (12, 26, 9), Bollinger Bands, rolling 20-day annualized volatility, daily returns, and relative volume.
- **3-Class Forward Regimes**:
  - `UP`: Forward 5-day return $> +1.5\%$
  - `DOWN`: Forward 5-day return $< -1.5\%$
  - `NEUTRAL`: Rangebound within $[-1.5\%, +1.5\%]$
- **Realistic Backtesting**: Enforces non-overlapping 5-day trade locks, 10 basis points ($0.10\%$) roundtrip friction/slippage, and max 25% portfolio position sizing.

### 3. Multi-Horizon Time-Series Forecasting (Prophet & Dual-Engine LSTM)
- **Facebook Prophet Engine**: Additive regression model decomposing price action into piecewise linear trends, yearly/monthly/weekly Fourier seasonality, and holiday changepoints.
- **Dual-Engine LSTM / Recurrent Forecaster**:
  - *Primary*: TensorFlow/Keras sequential LSTM with dropout and early stopping.
  - *Cloud-Optimized Fallback*: High-performance pure NumPy autoregressive recurrent sequence model (`_forecast_numpy`) tailored for 512MB RAM container environments (Render), computing holdout $MAE$ and $RMSE$ in under $0.1$ seconds.

### 4. Grounded AI Financial Copilot & Semantic Catalog
- **Semantic Item Price Parser (`item_pricing.py`)**: Automatically resolves consumer item inquiries (e.g., `"iPhone 16 Pro"` $\rightarrow$ ₹125,000, `"MacBook Pro"` $\rightarrow$ ₹199,900, `"Royal Enfield"` $\rightarrow$ ₹220,000) directly into balance and runway impact evaluations.
- **Tool-First Determinism**: Queries real user accounts, upcoming bills, and monthly cash flow to perform arithmetic checks before formatting guidance.
- **Offline Reasoning Fallback**: When external LLM API keys (Gemini / OpenAI) are absent, the system switches to deterministic financial reasoning with zero hallucinations.

### 5. Multi-Layer Transaction Anomaly Detection
- **4-Layer Defense**:
  1. *Layer 1*: Rolling Z-Score & Interquartile Range (IQR) outliers.
  2. *Layer 2*: Unsupervised Isolation Forest, One-Class SVM, and Reconstruction Autoencoder.
  3. *Layer 3*: Temporal LSTM Sequence Autoencoder.
  4. *Layer 4*: XGBoost Stacking Meta-Classifier with SHAP explanations.

---

## Module Directory Structure

```text
finpulse-ai/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py               # Non-blocking auth & permissive guest resolver
│   │   │   ├── v1/
│   │   │   │   ├── markets.py        # Public live market overview, quotes, analytics
│   │   │   │   ├── copilot.py        # Grounded AI copilot & item pricing parser
│   │   │   │   ├── transactions.py   # CSV import & ledger management
│   │   │   │   └── ...
│   │   ├── services/
│   │   │   ├── market_data/          # YFinanceProvider & UpstoxProvider engines
│   │   │   └── technical_analysis.py # Point-in-time SMA, EMA, RSI, MACD calculator
│   │   ├── ml/
│   │   │   ├── forecasting/          # ProphetService & LSTMService (with NumPy fallback)
│   │   │   ├── pipeline/             # Data ingestion, feature engineering, XGBoost training
│   │   │   └── anomaly/              # Multi-layer fraud and anomaly detection
│   │   └── main.py                   # FastAPI app with SPA route isolation
│   └── requirements.txt              # Cloud-optimized production dependencies
├── src/                              # React 19 Frontend
│   ├── pages/
│   │   ├── MarketsPage.tsx           # Real-time indices, sectors, and top equities
│   │   ├── ResearchPage.tsx          # Technical overlays & ML comparative laboratory
│   │   ├── CopilotPage.tsx           # Conversational financial copilot
│   │   └── ...
│   └── lib/api/                      # Resilient API clients with offline fallbacks
├── FINPULSE_REPORT.txt               # Comprehensive 700-line architecture & ML report
└── PROJECT_DEEP_DIVE_REPORT.txt      # Mirrored detailed engineering report
```

---

## Empirical Benchmark Evaluation

Evaluated out-of-sample on the untouched historical test partition (3,476 observations):

| Model / Baseline Strategy | Accuracy | Macro F1 | Technical Notes |
| :--- | :---: | :---: | :--- |
| **Random Guessing (Theoretical)** | ~33.33% | ~0.333 | Theoretical uniform 3-class expectation |
| **Always Majority Class ("UP")** | 35.50% | 0.175 | Unconditionally predicts training majority class |
| **5-Day Momentum Persistence** | 34.32% | 0.335 | Trend continuation heuristic |
| **XGBoost 3-Class Classifier** | **33.46%** | **0.325** | Point-in-time indicators with chronological split |
| **Binary 2-Class Formulation (UP vs Not-UP)** | **63.95%** | **0.404** | Binary regime classification |

### Out-of-Sample Backtesting Summary
- **Starting Capital**: ₹100,000.00
- **Final Portfolio Value**: ₹107,216.67 (+7.22% return)
- **Completed Non-Overlapping Trades**: 136 trades (48.5% win rate)
- **Transaction Friction**: 0.10% (10 basis points) deducted per trade
- **Max Drawdown**: -16.46%
- *Academic Note*: The model underperforms buy-and-hold (+8.98%) due to transaction costs and false-positive churn, faithfully demonstrating real market friction.

---

## Quick Start & Local Execution

### 1. Backend Setup
```bash
cd backend
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install cloud-optimized dependencies
pip install -r requirements.txt

# Start the API server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
# From project root
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

### 3. Running the Machine Learning Pipeline
All pipeline stages can be executed independently from `backend/`:
```bash
cd backend

# Collect historical market data (or generate synthetic GBM sample data)
python -m app.ml.pipeline.collect_data

# Compute 13 point-in-time technical features
python -m app.ml.pipeline.build_features

# Generate 5-day forward return labels
python -m app.ml.pipeline.build_targets

# Train XGBoost classifier & evaluate against naive baselines
python -m app.ml.pipeline.train_xgboost

# Run vectorized walk-forward backtest
python -m app.ml.pipeline.backtest
```

---

## Cloud Deployment (Render / Docker)

The project is pre-configured for automated one-click deployment on Render via [render.yaml](render.yaml):
- **Build Command**: `./build.sh` (builds the React frontend with Vite, then installs backend requirements)
- **Runtime**: Serves both the compiled SPA frontend and the FastAPI REST API from a single unified Uvicorn server.
- **Resource Footprint**: Memory usage stays well below Render's 512MB RAM free-tier limit.

---

## License & Third-Party Attributions

- Project code is licensed under the [MIT License](LICENSE).
- Vendored research components in `backend/app/ml/qlib_integration/` are adapted from [Microsoft Qlib](https://github.com/microsoft/qlib), Copyright © Microsoft Corporation (MIT License).
