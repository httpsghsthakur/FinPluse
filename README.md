# FinPulse AI — Market Intelligence & Financial Copilot

<div align="center">

[![CI/CD Pipeline](https://img.shields.io/github/actions/workflow/status/httpsghsthakur/Finpluse/ci.yml?branch=main&label=CI%2FCD&style=for-the-badge&logo=githubactions)](https://github.com/httpsghsthakur/Finpluse/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19.0-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![XGBoost](https://img.shields.io/badge/XGBoost-2.0-blue?style=for-the-badge)
![Pytest](https://img.shields.io/badge/Tests-Passing_100%25-success?style=for-the-badge&logo=pytest&logoColor=white)

**An AI-powered Market Intelligence platform combining technical analysis, machine learning prediction pipelines, real-time market snapshots, and personal finance management.**

</div>

---

## Overview

**FinPulse AI** represents a structural pivot from a standard expense tracker to a full-fledged quantitative financial intelligence platform. It ingests live market data, computes deterministic technical indicators, and trains machine learning models to forecast 5-day directional trends and expected volatility.

```text
┌─────────────────────────────────────────────────────────────┐
│                    FinPulse AI Architecture                 │
└─────────────────────────────────────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
     React 19 + TypeScript             FastAPI Backend
       (Port: 5173)                      (Port: 8000)
               │                               │
               │        REST API               │
               └───────────────┬───────────────┘
                               ▼
                  ┌─────────────────────────┐
                  │   Data & ML Pipeline    │
                  ├─────────────────────────┤
                  │ • Upstox Market Data    │
                  │ • Vectorized Tech Anal. │
                  │ • XGBoost Directional   │
                  │ • Walk-Forward Backtest │
                  │ • RAG / AI Copilot      │
                  └─────────────────────────┘
```

---

## Key Features

### 1. Market Intelligence Dashboard
- **Live Snapshots**: Real-time quotes for NIFTY 50, BANK NIFTY, SENSEX, and INDIA VIX.
- **AI Market Outlook**: XGBoost-powered predictive probabilities for 5-day market directions (UP/NEUTRAL/DOWN) with projected volatility and risk analysis.
- **Top Movers & Watchlist**: Embedded sparklines and technical trend detection.

### 2. Full-Scale ML Training Pipeline
- **Data Ingestion**: Programmatic ingestion of historical OHLCV candles via Upstox API.
- **Point-in-Time Features**: Strict lag-shifted feature generation (SMA, RSI, MACD, Bollinger Bands, rolling volatility) preventing look-ahead leakage.
- **Target Generation**: Automated directional classifications based on parameterized return thresholds.
- **Backtesting Engine**: Built-in chronological walk-forward testing engine calculating accurate PnL factoring in transaction slippage.

### 3. Personal Finance (Legacy Module)
- Maintained as a secondary module tracking Liquid Net Worth, expense categorization, and multi-horizon cash flow projections.

---

## The ML Pipeline (`backend/app/ml/pipeline/`)

We have engineered a strict 5-stage pipeline for stock prediction:

1. **`collect_data.py`**: Ingests historical data and stores as `parquet`.
2. **`build_features.py`**: Computes price-derived and technical features, safely shifted by `t-1`.
3. **`build_targets.py`**: Computes the true forward-looking 5-day return targets.
4. **`train_xgboost.py`**: Executes chronological splits, fits the XGBoost classifier, extracts SHAP feature importance, and serializes the `.joblib` model.
5. **`backtest.py`**: Runs a historical simulation using the trained model to calculate simulated portfolio returns.

### Pipeline Execution
```bash
cd backend
python -m app.ml.pipeline.collect_data
python -m app.ml.pipeline.build_features
python -m app.ml.pipeline.build_targets
python -m app.ml.pipeline.train_xgboost
python -m app.ml.pipeline.backtest
```

---

## Quick Start

### 1. Start the FastAPI Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. Start the React Frontend
```bash
# In a new terminal (from project root)
npm install
npm run dev
```
Access the dashboard at `http://localhost:5173`.

---

## Tech Stack
- **Frontend**: React 19, TypeScript, Tailwind CSS, Zustand, Recharts, Lucide Icons.
- **Backend**: FastAPI, SQLAlchemy 2.0 (Async), PostgreSQL/SQLite.
- **Machine Learning**: XGBoost, Scikit-Learn, Pandas, NumPy, PyArrow.
- **Data Providers**: Upstox API (V3).

---

## Contributing & License
Contributions are welcome! Please feel free to submit a Pull Request.
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
