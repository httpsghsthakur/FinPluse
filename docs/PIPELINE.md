# FinPulse AI — Machine Learning Pipeline Guide

This document details the quantitative machine learning pipeline implemented in `backend/app/ml/pipeline/`.

---

## 1. Pipeline Overview & Prediction Timing

The pipeline predicts the forward **5-day directional movement** of Indian equity instruments (NIFTY 50 large-cap constituents).

```
Day t Close (15:30 IST) ──> Features Computed (SMA, RSI, MACD, etc.)
                                 │
                                 ▼
                     XGBoost Directional Model
                                 │
                                 ▼
                     Target: Return from t to t+5
                     (Close_{t+5} - Close_t) / Close_t
```

### Exact Timing Formulation
- **Point-in-Time Features**: All indicators at row $t$ are computed using closing prices and volumes strictly $\le t$.
- **Target Horizon**: Measures return over the window $(t, t+5]$:
  $$\text{Return}_{5d} = \frac{\text{Close}_{t+5} - \text{Close}_t}{\text{Close}_t}$$
- **Zero Lookahead Leakage**: No data from day $t+1$ onwards is ever accessible during feature calculation.
- **Why No Lag-1 Shift**: Because features summarize the market at day $t$ close and the target is the subsequent return over $(t, t+5]$, an artificial $t-1$ lag would create a stale 1-day information delay.

---

## 2. Pipeline Stages & File Inventory

| Stage | Script | Input Files | Output Files | Key Operation |
| :--- | :--- | :--- | :--- | :--- |
| **1. Collect** | `collect_data.py` | Upstox API or Simulator | `data/raw/master_market_dataset.parquet` or `data/sample/synthetic_market_dataset.parquet` | Fetches daily OHLCV candles, normalizes timestamps to calendar dates, isolates synthetic samples. |
| **2. Features** | `build_features.py` | Market dataset (raw or sample) | `data/processed/features.parquet` | Generates 13 point-in-time technical features per instrument. |
| **3. Targets** | `build_targets.py` | `features.parquet` | `data/processed/dataset_with_targets.parquet` | Calculates forward 5d returns, realized volatility, and assigns UP/NEUTRAL/DOWN targets. |
| **4. Train** | `train_xgboost.py` | `dataset_with_targets.parquet` | `models/xgboost_direction.json`<br>`models/xgboost_direction.joblib`<br>`models/metrics.json`<br>`models/confusion_matrix.png` | 70/15/15 chronological split, fits unweighted XGBoost, evaluates against naive baselines. |
| **5. Backtest** | `backtest.py` | `dataset_with_targets.parquet` | Terminal report / PnL | Vectorized out-of-sample simulation with non-overlapping positions and transaction costs. |

---

## 3. Chronological Train / Validation / Test Split

To prevent look-ahead bias across partitions, data is partitioned strictly by unique calendar dates:

```
2022-01-21 ──────────────── 2025-05-02 ─── 2025-05-05 ────── 2026-01-15 ─── 2026-01-16 ────── 2026-09-30
           Train (70%)                            Val (15%)                          Test (15%)
           3,424 rows                             736 rows                           736 rows
```

- **Temporal Order Constraint**:
  $$\max(\text{Train Date}) < \min(\text{Val Date}) < \min(\text{Test Date})$$
- The **Test Set is kept strictly untouched** during feature scaling and model training.

---

## 4. How to Read `models/metrics.json`

The file `backend/app/ml/pipeline/models/metrics.json` contains comprehensive out-of-sample evaluation:

### 1. 3-Class XGBoost Metrics (`xgboost_3class_test_metrics`)
- **`accuracy`**: Fraction of test observations where the predicted class matched the true return regime.
- **`per_class`**:
  - `precision`: Out of all instances where model predicted class $C$, how many were actually $C$?
  - `recall`: Out of all true instances of class $C$, how many did the model identify?
  - `f1_score`: Harmonic mean of precision and recall.
  - `support`: Number of true instances of class $C$ in the test set.
- **`confusion_matrix`**: Rows represent True classes (`[DOWN, NEUTRAL, UP]`); columns represent Predicted classes.

### 2. Naive Baseline Comparisons (`naive_baselines`)
- **`majority_class`**: Always predicting the most frequent training class ("UP"). An ML model must meaningfully outperform this to claim predictive value.
- **`momentum_5d_persistence`**: Predicting that the forward 5-day return will continue in the direction of the prior 5-day return (`return_5d`).

### 3. Binary Experiment (`binary_up_vs_not_up_experiment`)
- An optional 2-class experiment testing whether the model can discern between positive breakouts ("UP") versus stagnating/declining markets ("Not-UP").

---

## 5. Limitations & Viva Talking Points

When presenting this project during a viva or evaluation:
1. **Low Signal in Daily Technical Indicators**: Asset returns are close to martingale difference sequences. Moving averages and RSI alone do not possess strong persistent alpha; accuracy near 35% on a 3-class problem is mathematically normal.
2. **Transaction Friction Matters**: While theoretical backtests without costs can appear profitable, factoring in realistic slippage and brokerage (10 bps per trade) reduces net alpha significantly.
3. **Execution Safety**: Live trading requires order-book depth, latency control, and risk management that cannot be simulated purely from daily EOD closes.
