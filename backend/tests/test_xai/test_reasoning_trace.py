"""Tests for reasoning traces and audit log."""
import pytest
from app.xai.reasoning_trace import ReasoningTrace, create_forecast_trace
from app.xai.audit_log import AuditLog


class TestReasoningTrace:
    def test_basic_trace(self):
        trace = ReasoningTrace("test_op", "user-1")
        trace.add_step("Step 1", "Did something", data={"key": "value"})
        trace.add_step("Step 2", "Did another thing")
        result = trace.finalize("output")
        assert result["operation"] == "test_op"
        assert len(result["steps"]) == 2

    def test_forecast_trace(self):
        trace = create_forecast_trace(
            "user-1", n_transactions=234, n_features=47,
            model_name="Prophet", mape=0.043,
            point_estimate=5240.50, ci_lower=4700, ci_upper=5780,
        )
        assert trace["operation"] == "forecast"
        assert len(trace["steps"]) == 5


class TestAuditLog:
    def test_log_and_query(self):
        log = AuditLog()
        entry_id = log.log_decision(
            "user-1", "forecast", {"n_tx": 100}, {"balance": 5240}, "v2.0",
        )
        entries = log.get_entries(user_id="user-1")
        assert len(entries) == 1
        assert entries[0]["id"] == entry_id

    def test_add_feedback(self):
        log = AuditLog()
        entry_id = log.log_decision("user-1", "anomaly", {}, {}, "v2.0")
        assert log.add_feedback(entry_id, "helpful")
        entries = log.get_entries(user_id="user-1")
        assert entries[0]["user_feedback"] == "helpful"

    def test_export_csv(self):
        log = AuditLog()
        log.log_decision("user-1", "forecast", {}, {}, "v2.0")
        csv_data = log.export_csv("user-1")
        assert "forecast" in csv_data
        assert "user-1" in csv_data
