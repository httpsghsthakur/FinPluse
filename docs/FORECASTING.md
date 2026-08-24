# Finpluse Forecasting Architecture

## Overview

Multi-horizon probabilistic cash flow forecasting using an ensemble of 4 models
with dynamic MAPE-based weighting.

## Models

| Model | Type | Strengths | Typical MAPE |
|-------|------|-----------|-------------|
| Prophet | Statistical | Seasonality, holidays, changepoints | 4-8% |
| N-BEATS | Neural | Pure time series, no feature engineering needed | 5-10% |
| N-HiTS | Neural | Multi-resolution, efficient long horizons | 4-9% |
| TFT | Neural | Multi-variate, attention-based, quantile outputs | 3-7% |

## Ensemble Strategy

The `WeightedEnsemble` dynamically weights models inversely proportional to their
recent MAPE on a 30-day holdout set. Weights are recomputed weekly.

## Feature Engineering

- **Lag features**: 1d, 7d, 14d, 30d rolling means and standard deviations
- **Calendar**: day_of_week, is_weekend, is_holiday (US federal), is_payday
- **Cyclical**: sin/cos encoding of month, day_of_week, day_of_month
- **Category velocity**: 7-day trend slope per spending category
- **Income stability**: Coefficient of variation of monthly income (90-day window)
- **Recurring detection**: Fourier analysis of per-merchant spending periodicity

## Scenario Engine

5 built-in scenarios + custom DSL:
1. **Job Loss**: Income to $0 for N days
2. **Medical Emergency**: One-time large expense
3. **Market Crash**: Investment portfolio decline
4. **Lifestyle Inflation**: Discretionary spending increase
5. **Side Income**: New income stream

All scenarios use Monte Carlo simulation (10,000 paths) for probabilistic outcomes.

## Training Pipeline

- **Cross-validation**: 5-fold TimeSeriesSplit with 7-day gap
- **Hyperparameter tuning**: Optuna (100 trials per model)
- **Experiment tracking**: MLflow-compatible logging
- **Auto-promotion**: Models with MAPE < 10% auto-promoted to production
- **Drift detection**: KS test on feature distributions, retrain if p < 0.05

## API

`POST /api/v2/forecast` -- See `data_validation.py` for request/response schemas.
