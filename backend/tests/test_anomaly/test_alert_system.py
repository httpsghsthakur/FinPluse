"""Tests for alert management system."""
import pytest
from app.ml.anomaly.alert_system import AlertManager


@pytest.fixture
def manager():
    return AlertManager(grouping_window_minutes=60)


class TestAlertManager:
    def test_create_alert(self, manager):
        alert = manager.create_alert(
            "user-1",
            {"amount": -500, "merchant": "Unknown Store", "date": "2026-08-20"},
            {"probability": 0.85, "severity": "CRITICAL", "fired_detectors": ["z_score"], "explanation": "test"},
        )
        assert alert is not None
        assert alert["severity"] == "CRITICAL"

    def test_suppress_low_score(self, manager):
        alert = manager.create_alert(
            "user-1",
            {"amount": -10, "merchant": "Cafe"},
            {"probability": 0.2, "severity": "INFO"},
        )
        assert alert is None  # Score too low

    def test_acknowledge_alert(self, manager):
        alert = manager.create_alert(
            "user-1",
            {"amount": -500, "merchant": "Store"},
            {"probability": 0.8, "severity": "CRITICAL", "fired_detectors": [], "explanation": ""},
        )
        assert manager.acknowledge_alert(alert["id"])
        alerts = manager.get_alerts("user-1", acknowledged=True)
        assert len(alerts) == 1

    def test_daily_digest(self, manager):
        manager.create_alert("user-1", {"amount": -500, "merchant": "A"},
                           {"probability": 0.8, "severity": "CRITICAL", "fired_detectors": [], "explanation": ""})
        manager.create_alert("user-1", {"amount": -300, "merchant": "B"},
                           {"probability": 0.6, "severity": "WARNING", "fired_detectors": [], "explanation": ""})
        digest = manager.get_daily_digest("user-1")
        assert digest["total_alerts"] == 2
        assert digest["by_severity"]["CRITICAL"] == 1
