"""
Finpluse v2 -- Behavioral Biometrics Collector
"""
from typing import List, Dict, Any
from pydantic import BaseModel

class BiometricPayload(BaseModel):
    user_id: str
    session_id: str
    typing_cadence: List[float]  # Inter-key intervals in ms
    mouse_velocity: List[float]  # Pixels/sec
    scroll_behavior: Dict[str, Any] # e.g., {"avg_speed": 12.5, "bounces": 2}
    time_of_day: int # Hour of day 0-23

def process_raw_biometrics(payload: BiometricPayload) -> Dict[str, float]:
    """Extract statistical features from raw biometric data."""
    features = {}
    
    # Typing cadence features
    if payload.typing_cadence:
        features["typing_mean"] = sum(payload.typing_cadence) / len(payload.typing_cadence)
        features["typing_var"] = sum((x - features["typing_mean"])**2 for x in payload.typing_cadence) / len(payload.typing_cadence)
    else:
        features["typing_mean"] = 0.0
        features["typing_var"] = 0.0
        
    # Mouse features
    if payload.mouse_velocity:
        features["mouse_mean"] = sum(payload.mouse_velocity) / len(payload.mouse_velocity)
        features["mouse_max"] = max(payload.mouse_velocity)
    else:
        features["mouse_mean"] = 0.0
        features["mouse_max"] = 0.0
        
    features["time_of_day"] = float(payload.time_of_day)
    
    return features
