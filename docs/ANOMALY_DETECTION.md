# Finpluse Anomaly Detection Architecture

## Multi-Layer Detection

| Layer | Detectors | Method |
|-------|-----------|--------|
| 1: Statistical | Z-Score, IQR, STL Seasonal | Threshold-based |
| 2: Machine Learning | Isolation Forest, One-Class SVM, Autoencoder | Model-based |
| 3: Sequence | LSTM Autoencoder, Transformer | Temporal patterns |
| 4: Meta | XGBoost Stacking | Ensemble of all scores |

## Alert Severity

- **INFO** (0.3-0.5): Unusual but probably legitimate
- **WARNING** (0.5-0.7): Likely anomaly, push notification
- **CRITICAL** (>0.7): High confidence fraud, immediate alert

## Smart Grouping

Alerts are grouped by merchant + time window (1 hour) to prevent alert fatigue.
Daily digest mode summarizes all anomalies.
