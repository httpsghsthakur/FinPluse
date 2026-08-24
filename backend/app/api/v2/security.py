"""
Finpluse v2 -- Security & Biometrics API
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from app.api.deps import get_current_user
from app.db.models.user import User
from app.security.biometrics.collector import BiometricPayload, process_raw_biometrics
from app.security.biometrics.profiler import BiometricProfiler
from app.security.biometrics.fraud_detector import calculate_anomaly_score

router = APIRouter()
profiler = BiometricProfiler()

@router.post("/biometrics/log")
async def log_biometrics(
    payload: BiometricPayload,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Log continuous biometric features."""
    if str(current_user.id) != payload.user_id:
        raise HTTPException(status_code=403, detail="User mismatch")
        
    features = process_raw_biometrics(payload)
    
    # Calculate anomaly score BEFORE updating profile to catch deviations
    profile = profiler.get_profile(payload.user_id)
    anomaly_score = calculate_anomaly_score(features, profile) if profile else 0.0
    
    # Async profile update
    background_tasks.add_task(profiler.update_profile, payload.user_id, features)
    
    return {
        "status": "success",
        "anomaly_score": anomaly_score,
        "action": "CHALLENGE" if anomaly_score > 0.8 else "ALLOW"
    }

