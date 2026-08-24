import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.ml.anomaly.ml_detectors import EnhancedIsolationForest

def generate_synthetic_transactions():
    np.random.seed(42)
    dates = [datetime(2026, 1, 1) + timedelta(days=i) for i in range(100)]
    
    data = {
        'date': dates,
        'amount': np.random.normal(50, 15, 100).tolist()
    }
    
    df = pd.DataFrame(data)
    df['is_anomaly'] = False
    
    # Inject anomalies
    # 1. Very high amount
    df.loc[90, 'amount'] = 5000.0
    df.loc[90, 'is_anomaly'] = True
    
    # 2. Very low but unusual sequence
    df.loc[91, 'amount'] = 4500.0
    df.loc[91, 'is_anomaly'] = True
    
    return df

def test_isolation_forest_precision_recall():
    df = generate_synthetic_transactions()
    
    # Fit the model
    detector = EnhancedIsolationForest(contamination=0.03, n_estimators=100)
    detector.fit(df)
    
    # Predict anomalies
    predictions = []
    
    # In real usage, we would score row by row or bulk score.
    # The EnhancedIsolationForest exposes 'score' method for a single transaction.
    # We will simulate bulk scoring for the test metric.
    
    # Let's directly use the fitted model for scoring
    X = detector._extract_features(df)
    X_scaled = detector._scaler.transform(X)
    
    # -1 for anomaly, 1 for normal
    preds = detector._model.predict(X_scaled)
    df['pred_anomaly'] = preds == -1
    
    true_anomalies = df['is_anomaly'].sum()
    detected_anomalies = df['pred_anomaly'].sum()
    
    true_positives = (df['is_anomaly'] & df['pred_anomaly']).sum()
    false_positives = (~df['is_anomaly'] & df['pred_anomaly']).sum()
    false_negatives = (df['is_anomaly'] & ~df['pred_anomaly']).sum()
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    
    print(f"\n[Isolation Forest Metrics]")
    print(f"Precision: {precision:.2f}")
    print(f"Recall: {recall:.2f}")
    print(f"True Positives: {true_positives}")
    print(f"False Positives: {false_positives}")
    print(f"False Negatives: {false_negatives}")
    
    # We expect high recall for the extreme outliers
    assert recall >= 0.90, "Recall is too low"
