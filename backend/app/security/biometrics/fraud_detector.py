"""
Finpluse v2 -- Biometric Fraud Detector
"""
import math

def calculate_anomaly_score(features: dict[str, float], profile: dict) -> float:
    """
    Calculate anomaly score using a simplified Mahalanobis distance proxy.
    Returns a score between 0.0 (normal) and 1.0 (highly anomalous).
    """
    if not profile:
        return 0.0 # Can't score without a profile
        
    total_z_score = 0.0
    feature_count = 0
    
    for k, v in features.items():
        if k in profile and profile[k]["var"] > 0:
            mean = profile[k]["mean"]
            std = math.sqrt(profile[k]["var"])
            z_score = abs(v - mean) / std
            total_z_score += z_score
            feature_count += 1
            
    if feature_count == 0:
        return 0.0
        
    avg_z = total_z_score / feature_count
    
    # Map z-score to 0-1 probability using sigmoid-like squashing
    # An avg z-score > 3 is considered highly anomalous
    score = 1.0 - math.exp(-avg_z / 2.0)
    return min(max(score, 0.0), 1.0)
