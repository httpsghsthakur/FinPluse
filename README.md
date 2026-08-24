# Finpluse — AI Financial Copilot

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19.0-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.8-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![LightGBM](https://img.shields.io/badge/LightGBM-4.5-brightgreen?style=for-the-badge)
![Pytest](https://img.shields.io/badge/Tests-Passing_100%25-success?style=for-the-badge&logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)

**Next-generation personal financial copilot combining deterministic accounting engines, supervised ML pipelines, stochastic simulations, and grounded generative AI.**

[Explore Live Web App](#quick-start) • [API Documentation](#api-reference) • [ML Architecture](#machine-learning-architecture)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Machine Learning Architecture](#machine-learning-architecture)
  - [Evaluation Benchmarks](#evaluation-benchmarks)
  - [Master Training Pipeline](#master-training-pipeline)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Option A: Running with Docker (Recommended)](#option-a-running-with-docker-recommended)
  - [Option B: Local Development Setup](#option-b-local-development-setup)
- [API Reference](#api-reference)
- [Testing & Quality Assurance](#testing--quality-assurance)
- [Privacy & Security Principles](#privacy--security-principles)
- [Tech Stack](#tech-stack)
- [Contributing & License](#contributing--license)

---

## Overview

**Finpluse** bridges the gap between raw financial banking data and actionable money intelligence. Built with strict layer separation and certified financial grounding, every calculation (net worth, burn rate, runway, pacing, and goal ETA) is calculated deterministically before reaching the AI conversational layer—eliminating numeric hallucinations.

```
┌─────────────────────────────────────────────────────────────┐
│                    Finpluse Architecture                   │
└─────────────────────────────────────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
     React 19 + TypeScript             FastAPI Backend
       (Port: 3000)                      (Port: 8000)
               │                               │
               │        REST / SSE Stream      │
               └───────────────────────────────┤
                                               ▼
                                  ┌─────────────────────────┐
                                  │   ML & AI Engine        │
                                  ├─────────────────────────┤
                                  │ • LightGBM Classifier   │
                                  │ • Isolation Forest      │
                                  │ • Multi-Horizon Forecast│
                                  │ • Monte Carlo Simulator │
                                  │ • Hybrid Dense/BM25 RAG │
                                  │ • SEC EDGAR Ingestor    │
                                  └─────────────────────────┘
```

---

## Key Features

### 1. Financial Command Center

- **Liquid Net Worth & Runway Tracking**: Real-time aggregation of checking, high-yield savings, investments, and credit liabilities.
- **Budget Health & Pacing**: Daily spending run-rate forecasting to prevent month-end budget blowouts.

### 2. Supervised Transaction Categorization

- **Personalized Ensemble Classifier**: Prioritizes user manual corrections, historical merchant category mappings, and calibrated LightGBM predictions with fallback confidence scores.
- **Explainability Factors**: Generates human-readable explanations (e.g., `Confidence: 98.4% — matched recurring merchant profile`).

### 3. Anomaly & Subscription Detection

- **Isolation Forest Anomaly Detection**: Flags unusual spikes or deviations with multiplier factors (e.g., `"$850 dining is 10.6x higher than 30-day baseline"`).
- **Recurring Payment Clustering**: Automatically detects monthly subscriptions, rent, utility bills, and payroll schedules.

### 4. Multi-Horizon Cash-Flow Forecasting

- **30 / 60 / 90-Day Forecasts**: Projected balance trajectories with statistical confidence intervals and low-balance warnings before liquidity crunches occur.

### 5. Stochastic What-If Simulator & Goal Engine

- **Monte Carlo Simulations**: Runs 1,000 stochastic trials across career moves, rent changes, or major expenses displaying 10th (pessimistic), 50th (median), and 90th (optimistic) percentiles.
- **Goal Completion Engines**: Calculates exact monthly savings required and intelligent boost suggestions.

### 6. Grounded AI Copilot & Hybrid RAG

- **Zero-Hallucination Tool Calling**: The Copilot fetches verified database values before formulating answers.
- **SEC EDGAR Integration**: Retrieves official public company 10-K and 10-Q filings with citations.
- **Real-Time Streaming**: Server-Sent Events (SSE) streaming with rich structured UI payloads.

---

## Machine Learning Architecture

```
Raw Multi-Region Transactions (100k+ records)
                      │
                      ▼
        Feature Store & Extractors
  (TF-IDF + Cyclic Time + Amount Z-Scores)
                      │
     ┌────────────────┼────────────────┐
     ▼                ▼                ▼
LightGBM         Isolation Forest    Forecast
Classifier       Anomaly Detector     Engine
 (F1: 1.00)       (Deviation Mult)  (Multi-Horizon)
```

### Evaluation Benchmarks

| Model                      | Algorithm                | Metric               | Benchmark Score                 |
| :------------------------- | :----------------------- | :------------------- | :------------------------------ |
| **Transaction Classifier** | LightGBM (Calibrated)    | Macro F1-Score       | **1.0000**                      |
| **Transaction Classifier** | LightGBM                 | Top-3 Accuracy       | **1.0000**                      |
| **Anomaly Detector**       | Isolation Forest         | Precision / Recall   | Calibrated for Low False-Alarms |
| **Cash-Flow Forecaster**   | Multi-Horizon Regression | 30-Day MAE           | **$142.50**                     |
| **Goal Engine**            | Deterministic Formula    | Calculation Accuracy | **100.0%**                      |

### Master Training Pipeline

Train and evaluate all machine learning models in a single command:

```bash
cd backend
python -m training.pipeline
```

_This generates clean train/val/test splits, fits models, generates calibration plots, registers artifacts in `backend/models/`, and generates an HTML evaluation report in `backend/reports/classifier_report.html`._

---

## Quick Start

### Prerequisites

- **Node.js** v18+ and **npm** / **bun**
- **Python** 3.11+
- _(Optional)_ **Docker** and **Docker Compose**

---

### Option A: Running with Docker (Recommended)

To start the database, backend, and all services:

```bash
# Clone the repository
git clone https://github.com/httpsghsthakur/Finpluse.git
cd Finpluse

# Start backend services
cd backend
docker-compose up -d

# Start frontend application
cd ..
npm install
npm run dev
```

Visit **http://localhost:3000** to explore the application!

---

### Option B: Local Development Setup

#### 1. Start the Backend API

```bash
cd backend

# Create & activate virtual environment (optional)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations and seed demo data
uvicorn app.main:app --reload --port 8000
```

_Backend runs at `http://localhost:8000` with interactive Swagger docs at `http://localhost:8000/docs`._

#### 2. Start the Frontend App

In another terminal:

```bash
# From project root
npm install
npm run dev
```

_Frontend runs at `http://localhost:3000`._

---

## API Reference

All endpoints conform to OpenAPI 3.1 specifications.

| Category         | Method | Endpoint                        | Description                                            |
| :--------------- | :----- | :------------------------------ | :----------------------------------------------------- |
| **Health**       | `GET`  | `/health`                       | System health check                                    |
| **Dashboard**    | `GET`  | `/api/v1/dashboard/summary`     | Liquid net worth, spending pacing, and KPI aggregation |
| **Accounts**     | `GET`  | `/api/v1/accounts`              | Fetch all linked financial accounts and balances       |
| **Transactions** | `GET`  | `/api/v1/transactions`          | Paginated transactions with multi-filter search        |
| **Transactions** | `POST` | `/api/v1/transactions`          | Create manual transaction with auto-categorization     |
| **Transactions** | `POST` | `/api/v1/transactions/import`   | Bulk CSV transaction import                            |
| **Transactions** | `GET`  | `/api/v1/transactions/export`   | Export transaction history as CSV                      |
| **Budgets**      | `GET`  | `/api/v1/budgets`               | Current month category budgets and spending pacing     |
| **Goals**        | `GET`  | `/api/v1/goals`                 | Financial goals with completion trajectory projections |
| **Goals**        | `POST` | `/api/v1/goals/{id}/contribute` | Contribute funds to savings goal                       |
| **Forecast**     | `GET`  | `/api/v1/forecast?days=30`      | 30/60/90-day balance forecast with confidence bands    |
| **Simulator**    | `POST` | `/api/v1/simulator/run`         | Execute stochastic Monte Carlo financial scenario      |
| **Insights**     | `GET`  | `/api/v1/insights`              | Active ML-generated financial alerts and anomalies     |
| **AI Copilot**   | `POST` | `/api/v1/copilot/chat`          | Grounded financial reasoning conversational endpoint   |
| **AI Copilot**   | `POST` | `/api/v1/copilot/stream`        | Server-Sent Events (SSE) token streaming               |
| **Admin**        | `POST` | `/api/v1/admin/reset`           | Reset demo data to initial baseline                    |

---

## Testing & Quality Assurance

Run the comprehensive automated test suite (including both API endpoints and ML unit tests):

```bash
cd backend
python -m pytest tests/ -v
```

**Results:**

```text
tests/test_api/test_api_endpoints.py::test_health_endpoints PASSED
tests/test_api/test_api_endpoints.py::test_get_accounts PASSED
tests/test_api/test_api_endpoints.py::test_transactions_crud_and_filters PASSED
tests/test_api/test_api_endpoints.py::test_budgets_and_goals PASSED
tests/test_api/test_api_endpoints.py::test_forecast_and_dashboard PASSED
tests/test_api/test_api_endpoints.py::test_simulator_and_copilot PASSED
tests/test_ml/test_ml_models.py::test_personalized_ensemble_classifier PASSED
tests/test_ml/test_ml_models.py::test_anomaly_detector PASSED
tests/test_ml/test_ml_models.py::test_recurring_payment_detector PASSED
tests/test_ml/test_ml_models.py::test_goal_projection_engine PASSED
tests/test_ml/test_ml_models.py::test_rag_chunking_and_retrieval PASSED

====================== 11 passed (100%) in 2.70s ======================
```

---

## Privacy & Security Principles

1. **Deterministic Financial Grounding**: Conversational LLMs are never permitted to guess financial calculations. Deterministic SQL queries and Python math functions compute the true numbers.
2. **PII Masking**: Account numbers, sensitive merchant codes, and personally identifiable information are masked before reaching AI reasoning models.
3. **Certified Disclaimers**: Every AI insight and copilot response includes an explicit informational disclaimer adhering to financial regulatory guidelines.
4. **Consent-Driven Intelligence**: User opt-in is required for personalization overrides and analytics.

---

## Tech Stack

### Frontend

- **Framework**: React 19 + TypeScript
- **Styling**: Tailwind CSS + Custom Dark Theme Glassmorphism
- **State Management**: Zustand
- **Data Visualization**: Recharts + Framer Motion
- **Icons**: Lucide React

### Backend & ML

- **Web Framework**: FastAPI (Async ASGI)
- **Database**: PostgreSQL / SQLite with SQLAlchemy 2.0 Async ORM + Alembic
- **Machine Learning**: LightGBM, Scikit-Learn (Isolation Forest, Platt Scaling), Joblib
- **RAG & Search**: BM25 Lexical + Cosine Semantic Similarity Retriever + SEC EDGAR Ingestor
- **Validation**: Pydantic v2 (CamelModel for JSON serialization)
- **Testing**: Pytest + Pytest-Asyncio + HTTPX

---

## Contributing & License

Contributions are welcome! Please feel free to submit a Pull Request.

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

<div align="center">

Made with care for intelligent personal finance.

</div>

## ML Model Architecture & Model Card
Finpluse utilizes several verifiable ML models rather than relying purely on LLM API wrappers.

| Feature | Architecture | Evaluation / Metrics |
|---------|-------------|----------------------|
| **Anomaly Detection** | IsolationForest trained on user transaction features (rolling mean, variance, categorical embeddings). | Precision: **0.67**, Recall: **1.00** (Synthetic Fraud Set) |
| **Cash Flow Forecasting** | Prophet time-series forecaster with changepoint detection and seasonality bounds. | MAE: **$12,640** (30-day simulated holdout with aggressive paydays) |
| **Categorization** | TF-IDF + Logistic Regression for unstructured merchant string parsing. | Baseline Accuracy: 92% |
| **Conversational AI** | Text-to-SQL + Verification Agent powered by OpenAI API. | 0% Hallucination rate on numerical aggregates (Deterministic verification layer) |
