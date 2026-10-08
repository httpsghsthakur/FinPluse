# FinPulse AI — Model Artifacts & Environment Specification

## Pinned Library Versions
The serialized model artifacts in this directory were trained and exported using the following pinned environment:

| Dependency | Version | Purpose |
| :--- | :--- | :--- |
| **Python** | `3.12.10` | CPython runtime |
| **XGBoost** | `2.1.1` | Native gradient boosting engine (`xgboost_direction.json` & `.joblib`) |
| **scikit-learn** | `1.7.2` | Preprocessing (`LabelEncoder`), evaluation, metrics |
| **pandas** | `2.2.2` | Tabular data manipulation and datetime index management |
| **numpy** | `2.1.3` | Numerical arrays and random number generators |
| **joblib** | `1.4.2` | Python object serialization |

## Artifact Files

1. `xgboost_direction.json`
   - Native XGBoost Booster serialization format (`Booster.save_model`).
   - Forward/backward compatible across XGBoost releases without pickle vulnerability warnings.
2. `xgboost_direction.joblib`
   - Scikit-learn wrapper object saved for immediate compatibility with `scikit-learn` pipelines.
3. `label_encoder.joblib`
   - Fitted `sklearn.preprocessing.LabelEncoder` instance mapping classes: `['DOWN', 'NEUTRAL', 'UP']` to `[0, 1, 2]`.
4. `features.joblib`
   - Serialized list of the 13 exact feature names in expected column order.
5. `metrics.json`
   - Comprehensive out-of-sample evaluation metrics: accuracy, per-class precision/recall/F1, confusion matrix, naive baseline comparisons, and feature importance.
6. `confusion_matrix.png`
   - Visual heatmap of out-of-sample test set classification results.

## Model Interpretation & Honest Viva Limitations

- **Predictive Power**: Short-term directional forecasting of equity prices using backward-looking indicators (SMA, RSI, MACD, Bollinger Bands) exhibits accuracy near random-walk / naive baseline chance.
- **Overfitting Prevention**: Training uses an untouched 15% out-of-sample chronological test set. Never evaluate on the training partition.
- **Regulatory Disclaimer**: These models are educational prototypes designed for academic evaluation and do NOT constitute financial or investment advice.
