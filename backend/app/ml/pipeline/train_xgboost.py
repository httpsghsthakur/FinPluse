import os
import joblib
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
from sklearn.metrics import classification_report, accuracy_score
from app.core.logging import get_logger

logger = get_logger(__name__)

TARGET_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "processed", "dataset_with_targets.parquet")
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")

FEATURES = [
    'return_1d', 'return_5d', 'return_20d',
    'volatility_20d', 'sma_20', 'sma_50', 'sma_200',
    'rsi_14', 'macd', 'macd_signal',
    'relative_volume'
]

def train_xgboost():
    """Trains the baseline XGBoost directional model."""
    if not os.path.exists(TARGET_DATA_PATH):
        logger.error("Target dataset not found. Run build_targets.py first.")
        return
        
    df = pd.read_parquet(TARGET_DATA_PATH)
    df = df.dropna(subset=FEATURES)
    
    logger.info(f"Dataset shape after dropping missing features: {df.shape}")
    
    # Chronological Split (Train: <2025, Val: 2025)
    # Using simple date thresholds for demonstration
    split_date = pd.Timestamp("2024-01-01")
    
    train_df = df[df.index < split_date]
    test_df = df[df.index >= split_date]
    
    logger.info(f"Train size: {len(train_df)}, Test size: {len(test_df)}")
    
    if len(train_df) == 0 or len(test_df) == 0:
        logger.error("Not enough data to perform chronological split.")
        return
        
    X_train, y_train_raw = train_df[FEATURES], train_df['target_direction']
    X_test, y_test_raw = test_df[FEATURES], test_df['target_direction']
    
    # Encode targets
    le = LabelEncoder()
    y_train = le.fit_transform(y_train_raw)
    y_test = le.transform(y_test_raw)
    
    # Handle Class Imbalance via sample weights (optional, basic approach)
    from sklearn.utils.class_weight import compute_sample_weight
    sample_weights = compute_sample_weight('balanced', y_train)
    
    # Train XGBoost
    logger.info("Training XGBoost Classifier...")
    clf = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        objective="multi:softprob"
    )
    
    clf.fit(X_train, y_train, sample_weight=sample_weights)
    
    # Evaluate
    preds = clf.predict(X_test)
    logger.info("\n" + classification_report(y_test, preds, target_names=le.classes_))
    
    # Feature Importance
    importance = pd.DataFrame({
        'feature': FEATURES,
        'importance': clf.feature_importances_
    }).sort_values('importance', ascending=False)
    logger.info(f"Top Features:\n{importance.head()}")
    
    # Save artifacts
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(clf, os.path.join(MODEL_DIR, "xgboost_direction.joblib"))
    joblib.dump(le, os.path.join(MODEL_DIR, "label_encoder.joblib"))
    joblib.dump(FEATURES, os.path.join(MODEL_DIR, "features.joblib"))
    
    logger.info("Model and artifacts saved successfully.")

if __name__ == "__main__":
    train_xgboost()
