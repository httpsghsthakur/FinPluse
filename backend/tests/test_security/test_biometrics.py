import pytest
from app.security.biometrics.collector import BiometricPayload, process_raw_biometrics
from app.security.biometrics.profiler import BiometricProfiler
from app.security.biometrics.fraud_detector import calculate_anomaly_score

def test_process_raw_biometrics():
    payload = BiometricPayload(
        user_id="test", session_id="123",
        typing_cadence=[100, 120, 110], mouse_velocity=[50, 60],
        scroll_behavior={"avg_speed": 10}, time_of_day=14
    )
    features = process_raw_biometrics(payload)
    assert features["typing_mean"] == 110.0
    assert features["mouse_max"] == 60.0

def test_anomaly_score():
    features = {"typing_mean": 110.0}
    profile = {"typing_mean": {"mean": 100.0, "var": 100.0, "count": 10}}
    score = calculate_anomaly_score(features, profile)
    # z = (110 - 100) / sqrt(100) = 1.0
    # score = 1 - exp(-1.0 / 2) = 1 - 0.606 = 0.393
    assert 0.3 < score < 0.5
