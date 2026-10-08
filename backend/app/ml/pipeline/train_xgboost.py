"""
FinPulse AI — XGBoost Market Direction Classifier.

Training, Validation, and Evaluation Pipeline:
---------------------------------------------
1. Configurable Chronological Split:
   - Divides unique historical dates into Train (70%), Validation (15%), Test (15%).
   - Strict temporal ordering: max(train_date) < min(val_date) < min(test_date).
   - Test set is kept untouched during model fitting.
2. Evaluation & Baselines:
   - Model test accuracy, per-class Precision/Recall/F1, and Confusion Matrix.
   - Always-Majority-Class Baseline.
   - 5-Day Momentum Baseline (same direction as past 5 days).
   - Optional 2-Class (UP vs Not-UP) experimental comparison.
3. Artifact Persistence:
   - Native XGBoost Booster JSON and Joblib serialization.
   - Metrics saved to models/metrics.json.
   - Confusion matrix plot saved to models/confusion_matrix.png.
"""
from __future__ import annotations

import argparse
import json
import os
from typing import Dict, Any, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb

from app.core.logging import get_logger

logger = get_logger(__name__)

PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_DATA_PATH = os.path.join(PIPELINE_DIR, "data", "processed", "dataset_with_targets.parquet")
MODEL_DIR = os.path.join(PIPELINE_DIR, "models")

FEATURES = [
    'return_1d', 'return_5d', 'return_20d',
    'volatility_20d', 'sma_20', 'sma_50', 'sma_200',
    'rsi_14', 'macd', 'macd_signal',
    'bollinger_upper', 'bollinger_lower',
    'relative_volume'
]


def chronological_split(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split dataset chronologically by date across all instruments.
    Guarantees: max(train) < min(val) and max(val) < min(test).
    """
    unique_dates = np.array(sorted(df.index.unique()))
    n_dates = len(unique_dates)

    train_end_idx = int(n_dates * train_ratio)
    val_end_idx = int(n_dates * (train_ratio + val_ratio))

    train_cutoff = unique_dates[train_end_idx]
    val_cutoff = unique_dates[val_end_idx]

    train_df = df[df.index < train_cutoff].copy()
    val_df = df[(df.index >= train_cutoff) & (df.index < val_cutoff)].copy()
    test_df = df[df.index >= val_cutoff].copy()

    logger.info(
        f"Chronological Split (Dates: {n_dates} total):\n"
        f"  Train:      {len(train_df):5d} rows | {train_df.index.min().strftime('%Y-%m-%d')} -> {train_df.index.max().strftime('%Y-%m-%d')}\n"
        f"  Validation: {len(val_df):5d} rows | {val_df.index.min().strftime('%Y-%m-%d')} -> {val_df.index.max().strftime('%Y-%m-%d')}\n"
        f"  Test:       {len(test_df):5d} rows | {test_df.index.min().strftime('%Y-%m-%d')} -> {test_df.index.max().strftime('%Y-%m-%d')}"
    )

    return train_df, val_df, test_df


def plot_confusion_matrix(cm: np.ndarray, classes: list[str], output_path: str):
    """Save confusion matrix as a PNG heatmap."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(6, 5))
        cax = ax.matshow(cm, cmap=plt.cm.Blues, alpha=0.8)
        fig.colorbar(cax)

        ax.set_xticks(range(len(classes)))
        ax.set_yticks(range(len(classes)))
        ax.set_xticklabels(classes, fontsize=10)
        ax.set_yticklabels(classes, fontsize=10)
        ax.set_xlabel("Predicted Label", fontsize=11, labelpad=10)
        ax.set_ylabel("True Label", fontsize=11, labelpad=10)
        ax.set_title("XGBoost Test Set Confusion Matrix", fontsize=12, pad=15)

        for i in range(len(classes)):
            for j in range(len(classes)):
                ax.text(j, i, str(cm[i, j]), ha="center", va="center", color="black", fontsize=11)

        plt.tight_layout()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=150)
        plt.close()
        logger.info(f"Saved confusion matrix figure to {output_path}")
    except Exception as e:
        logger.warning(f"Could not render confusion matrix figure: {e}")


def train_xgboost(
    input_path: str | None = None,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
) -> Dict[str, Any]:
    """Train XGBoost direction classifier and compute honest baseline comparisons."""
    src_path = input_path or TARGET_DATA_PATH
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Target dataset not found at {src_path}. Run build_targets.py first.")

    df = pd.read_parquet(src_path)
    df = df.dropna(subset=FEATURES + ['target_direction'])
    logger.info(f"Dataset shape after dropping missing features: {df.shape}")

    # Chronological Split
    train_df, val_df, test_df = chronological_split(df, train_ratio=train_ratio, val_ratio=val_ratio)

    X_train, y_train_raw = train_df[FEATURES], train_df['target_direction']
    X_val, y_val_raw = val_df[FEATURES], val_df['target_direction']
    X_test, y_test_raw = test_df[FEATURES], test_df['target_direction']

    # Encode targets
    le = LabelEncoder()
    y_train = le.fit_transform(y_train_raw)
    y_val = le.transform(y_val_raw)
    y_test = le.transform(y_test_raw)
    classes = list(le.classes_)

    # Train 3-Class XGBoost
    # Note: Unweighted cross-entropy is used to preserve true empirical probabilities.
    # Artificial balanced sample weighting previously distorted class recall.
    logger.info("Training 3-Class XGBoost Classifier (unweighted, objective=multi:softprob)...")
    clf = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        objective="multi:softprob",
        eval_metric="mlogloss",
    )

    clf.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )

    # Predictions on unseen test set
    preds_test = clf.predict(X_test)
    test_acc = float(accuracy_score(y_test, preds_test))
    report_dict = classification_report(y_test, preds_test, target_names=classes, output_dict=True)
    report_text = classification_report(y_test, preds_test, target_names=classes)
    cm = confusion_matrix(y_test, preds_test)

    logger.info(f"\n=== TEST SET 3-CLASS EVALUATION ===\nAccuracy: {test_acc:.4f}\n{report_text}")
    print(f"\n=== TEST SET 3-CLASS EVALUATION ===\nAccuracy: {test_acc:.4f}\n{report_text}")

    # ── Naive Baselines on Test Set ───────────────────────────────────────────
    # 1. Always Majority Class
    majority_class_str = y_train_raw.mode()[0]
    majority_class_idx = int(le.transform([majority_class_str])[0])
    preds_majority = np.full_like(y_test, fill_value=majority_class_idx)
    acc_majority = float(accuracy_score(y_test, preds_majority))
    f1_majority = float(f1_score(y_test, preds_majority, average='macro'))

    # 2. 5-day Momentum / Persistence ("same direction as previous 5 days")
    def momentum_baseline(ret_5d: float) -> str:
        if ret_5d > 0.015:
            return "UP"
        elif ret_5d < -0.015:
            return "DOWN"
        return "NEUTRAL"

    preds_mom_raw = test_df['return_5d'].apply(momentum_baseline)
    preds_mom = le.transform(preds_mom_raw)
    acc_momentum = float(accuracy_score(y_test, preds_mom))
    f1_momentum = float(f1_score(y_test, preds_mom, average='macro'))

    baseline_msg = (
        f"\n=== NAIVE BASELINE COMPARISONS (TEST SET) ===\n"
        f"1. Majority Class ('{majority_class_str}'): Accuracy = {acc_majority:.4f}, Macro F1 = {f1_majority:.4f}\n"
        f"2. 5-Day Momentum Persistence:       Accuracy = {acc_momentum:.4f}, Macro F1 = {f1_momentum:.4f}\n"
        f"3. XGBoost 3-Class Classifier:         Accuracy = {test_acc:.4f}, Macro F1 = {report_dict['macro avg']['f1-score']:.4f}\n"
    )
    logger.info(baseline_msg)
    print(baseline_msg)

    # ── Feature Importances ───────────────────────────────────────────────────
    importance_df = pd.DataFrame({
        'feature': FEATURES,
        'importance': clf.feature_importances_
    }).sort_values('importance', ascending=False)
    logger.info(f"\nFeature Importances:\n{importance_df.to_string(index=False)}")

    # ── Optional 2-Class Experiment (UP vs Not-UP) ────────────────────────────
    logger.info("\nRunning optional 2-class experiment (UP vs Not-UP)...")
    y_train_bin = (y_train_raw == "UP").astype(int)
    y_val_bin = (y_val_raw == "UP").astype(int)
    y_test_bin = (y_test_raw == "UP").astype(int)

    clf_bin = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        objective="binary:logistic",
        eval_metric="logloss",
    )
    clf_bin.fit(X_train, y_train_bin, eval_set=[(X_val, y_val_bin)], verbose=False)
    preds_bin = clf_bin.predict(X_test)
    acc_bin = float(accuracy_score(y_test_bin, preds_bin))
    report_bin = classification_report(y_test_bin, preds_bin, target_names=["Not-UP", "UP"], output_dict=True)
    logger.info(f"2-Class Experiment Test Accuracy: {acc_bin:.4f}")

    # ── Save Artifacts ────────────────────────────────────────────────────────
    os.makedirs(MODEL_DIR, exist_ok=True)

    # Model saves: Native JSON and Joblib
    json_model_path = os.path.join(MODEL_DIR, "xgboost_direction.json")
    clf.get_booster().save_model(json_model_path)
    joblib.dump(clf, os.path.join(MODEL_DIR, "xgboost_direction.joblib"))
    joblib.dump(le, os.path.join(MODEL_DIR, "label_encoder.joblib"))
    joblib.dump(FEATURES, os.path.join(MODEL_DIR, "features.joblib"))

    # Save Confusion Matrix figure
    cm_fig_path = os.path.join(MODEL_DIR, "confusion_matrix.png")
    plot_confusion_matrix(cm, classes, cm_fig_path)

    # Compile metrics dictionary
    metrics_summary: Dict[str, Any] = {
        "dataset_split": {
            "train_rows": len(train_df),
            "train_date_range": [train_df.index.min().strftime('%Y-%m-%d'), train_df.index.max().strftime('%Y-%m-%d')],
            "val_rows": len(val_df),
            "val_date_range": [val_df.index.min().strftime('%Y-%m-%d'), val_df.index.max().strftime('%Y-%m-%d')],
            "test_rows": len(test_df),
            "test_date_range": [test_df.index.min().strftime('%Y-%m-%d'), test_df.index.max().strftime('%Y-%m-%d')],
        },
        "xgboost_3class_test_metrics": {
            "accuracy": test_acc,
            "macro_avg_precision": report_dict['macro avg']['precision'],
            "macro_avg_recall": report_dict['macro avg']['recall'],
            "macro_avg_f1": report_dict['macro avg']['f1-score'],
            "per_class": {
                c: {
                    "precision": report_dict[c]['precision'],
                    "recall": report_dict[c]['recall'],
                    "f1_score": report_dict[c]['f1-score'],
                    "support": int(report_dict[c]['support']),
                }
                for c in classes
            },
            "confusion_matrix": cm.tolist(),
            "classes": classes,
        },
        "naive_baselines": {
            "majority_class": {
                "class_chosen": majority_class_str,
                "accuracy": acc_majority,
                "macro_f1": f1_majority,
            },
            "momentum_5d_persistence": {
                "accuracy": acc_momentum,
                "macro_f1": f1_momentum,
            },
        },
        "binary_up_vs_not_up_experiment": {
            "accuracy": acc_bin,
            "classification_report": report_bin,
        },
        "top_features": importance_df.to_dict(orient="records"),
        "limitations": (
            "Financial asset prices exhibit near-random walk behavior over short horizons. "
            "Technical indicators (SMA, RSI, MACD, Bollinger) provide weak standalone signal. "
            "Predictive performance near naive baselines is expected and mathematically honest. "
            "This model is a proof-of-concept pipeline, not a profitable trading strategy."
        ),
    }

    metrics_path = os.path.join(MODEL_DIR, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)
    logger.info(f"Saved comprehensive evaluation metrics to {metrics_path}")

    return metrics_summary


def main():
    parser = argparse.ArgumentParser(description="Train XGBoost market direction model.")
    parser.add_argument("--input", type=str, default=None, help="Input target dataset parquet path.")
    parser.add_argument("--train-ratio", type=float, default=0.70, help="Train split ratio (default: 0.70).")
    parser.add_argument("--val-ratio", type=float, default=0.15, help="Validation split ratio (default: 0.15).")
    args = parser.parse_args()

    train_xgboost(input_path=args.input, train_ratio=args.train_ratio, val_ratio=args.val_ratio)


if __name__ == "__main__":
    main()
