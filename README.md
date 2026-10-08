# FinPulse AI — Market Intelligence & Financial Copilot

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19.0-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![XGBoost](https://img.shields.io/badge/XGBoost-2.1-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Project-Academic_Internship_Prototype-orange?style=for-the-badge)

**A student quantitative finance and machine learning prototype combining point-in-time technical analysis, gradient-boosted directional forecasting, walk-forward backtesting, and dashboard interfaces.**

</div>

---

## Academic & Engineering Integrity Statement

> [!NOTE]
> This project was developed as a student internship engineering submission. Honesty, methodology, and reproducibility are prioritized over inflated claims or data mining.
> - **No Future Leakage**: All technical indicators are evaluated strictly on historical bars available up to day $t$ close to predict forward returns from $t$ to $t+5$.
> - **Untouched Test Split**: Model metrics are reported on a strictly chronological out-of-sample test split (the final 15% of trading days).
> - **Naive Baselines**: Predictions are explicitly compared against majority-class and 5-day momentum persistence baselines.
> - **Explicit Sample Data**: If an active Upstox broker API token is not provided, the pipeline runs against clearly labeled synthetic sample data (`data/sample/`), never masquerading as real market data.

---

## System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    FinPulse AI Architecture                 │
└─────────────────────────────────────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
     React 19 + TypeScript             FastAPI Backend
       (Port: 5173 / 3000)               (Port: 8000)
               │                               │
               │        REST API               │
               └───────────────┬───────────────┘
                               ▼
                  ┌─────────────────────────┐
                  │   Data & ML Pipeline    │
                  ├─────────────────────────┤
                  │ • Upstox Ingestion /    │
                  │   Synthetic Sample Data │
                  │ • Point-in-Time Feats   │
                  │ • XGBoost 3-Class       │
                  │ • Vectorized Backtest   │
                  └─────────────────────────┘
```

---

## Module Classification: Core vs. Experimental

To ensure transparency during viva examination, the codebase is partitioned into active core functionality and experimental research scaffolds:

### 1. Core Modules (Active & Tested)
- **Market Data Pipeline (`backend/app/ml/pipeline/`)**:
  - `collect_data.py`: Ingestion from Upstox API with date normalization, or reproducible sample generation (`--synthetic`).
  - `build_features.py`: Point-in-time calculation of SMA (20, 50, 200), RSI (14), MACD (12, 26, 9), Bollinger Bands, rolling volatility, and relative volume.
  - `build_targets.py`: Forward 5-day percentage return $(Close_{t+5} - Close_t) / Close_t$, 3-class target labeling (UP, NEUTRAL, DOWN), and forward realized volatility.
  - `train_xgboost.py`: Chronological 70/15/15 split, unweighted XGBoost classifier, baseline comparisons, and artifact export.
  - `backtest.py`: Vectorized out-of-sample simulation enforcing non-overlapping 5-day positions and transaction costs.
  - `predict.py`: Inference service loading serialized native JSON and Joblib models.
- **Web Dashboard (`src/`, `backend/app/main.py`)**:
  - React/TypeScript frontend providing market overview, watchlists, technical charts, and simulation views.
  - FastAPI backend serving health probes, market quotes, and prediction endpoints.

### 2. Experimental Scaffolds (Prototypes / Non-Core)
- **Microsoft Qlib Integration (`backend/app/ml/qlib_integration/`)**: Vendored and adapted from [Microsoft/qlib](https://github.com/microsoft/qlib) under the MIT License. Included as an exploratory scaffold for deep neural architectures (ALSTM, Transformer); **not original work**.
- **Federated Learning (`backend/app/ml/federated/`, `src/lib/ml/FederatedClient.ts`)**: Proof-of-concept client-side gradient sharing scaffold.
- **Multi-Agent Orchestrator (`backend/app/agents/`)**: Experimental ReAct agent framework for LLM-assisted tool calling.
- **Multimodal Parsers (`backend/app/multimodal/`)**: Experimental receipt OCR and speech-to-text mocks.
- **Explainable AI (`backend/app/xai/`)**: Prototype reasoning traces and feature attribution stubs.
- **Personal Finance Module (`backend/app/db/models/portfolio.py`, etc.)**: Maintained as a secondary legacy module from initial project iterations.

---

## ML Pipeline Execution

All pipeline commands are executed from the `backend/` directory:

```bash
cd backend

# 1. Collect real Upstox market data (requires UPSTOX_ANALYTICS_TOKEN)
#    OR generate labeled synthetic sample data for development:
python -m app.ml.pipeline.collect_data --synthetic

# 2. Build point-in-time features (SMA, RSI, MACD, Bollinger, Volatility)
python -m app.ml.pipeline.build_features

# 3. Generate forward 5-day directional targets (UP / NEUTRAL / DOWN)
python -m app.ml.pipeline.build_targets

# 4. Train XGBoost classifier on chronological train split, evaluate on untouched test set
python -m app.ml.pipeline.train_xgboost

# 5. Run vectorized backtest on test partition with non-overlapping positions
python -m app.ml.pipeline.backtest
```

### Reproducibility via Makefile
A unified automation command is available:
```bash
make pipeline          # Runs full pipeline using available real or sample data
make pipeline-synthetic # Runs full pipeline end-to-end with synthetic sample data
```

---

## Benchmark Results & Empirical Evaluation

Evaluated out-of-sample on the test partition (736 observations, 2026-01-16 to 2026-09-30):

| Model / Baseline | Accuracy | Macro F1 | Note |
| :--- | :---: | :---: | :--- |
| **Random Guessing** | ~33.3% | ~0.333 | Theoretical uniform 3-class baseline |
| **Always Majority Class ("UP")** | 35.60% | 0.175 | Unconditionally predicts training majority class |
| **5-Day Momentum Persistence** | 36.14% | 0.361 | Predicts continuation of prior 5-day trend |
| **XGBoost 3-Class Classifier** | **34.92%** | **0.265** | Point-in-time indicators with chronological split |
| **Binary 2-Class Experiment (UP vs Not-UP)** | **52.85%** | **0.503** | Binary formulation near 50% coin-toss baseline |

### Backtesting Summary (Out-of-Sample Test Partition)
- **Initial Capital**: ₹100,000.00
- **Final Capital**: ₹107,216.67
- **Strategy Return**: +7.22% (136 completed non-overlapping trades, 48.5% win rate)
- **Buy & Hold Benchmark**: +8.98%
- **Max Drawdown**: -16.46%
- **Friction**: 0.10% (10 bps) transaction cost per trade

*The strategy underperformed buy-and-hold due to transaction friction and false-positive churn, reflecting realistic market dynamics.*

---

## Limitations & Risks

1. **Weak Signal-to-Noise Ratio**: Backward-looking technical indicators on daily equity bars carry limited directional edge over short horizons. Accuracies near naive baselines are mathematically expected.
2. **Small Universe**: Current ingestion universe is restricted to 4 major NIFTY large-cap constituents (RELIANCE, HDFCBANK, INFY, TCS).
3. **Execution Assumptions**: Backtest uses daily closing prices with a 10 bps fixed slippage proxy; real execution entails market-impact slippage, liquidity variations, and intraday gap risk.
4. **Prototype Status**: This software is an academic engineering internship demonstration. It is **not financial advice, investment advisory, or commercial software**.

---

## Quick Start

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # Configure local parameters
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
# From project root
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## License & Third-Party Attributions

- Project code is licensed under the [MIT License](LICENSE).
- Vendored deep learning models in `backend/app/ml/qlib_integration/` are adapted from [Microsoft Qlib](https://github.com/microsoft/qlib), Copyright © Microsoft Corporation (MIT License).
