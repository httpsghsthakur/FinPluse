"""Tests for the scenario engine and built-in scenarios."""
import pytest
from app.ml.forecasting.v2.scenario_engine import (
    ScenarioBuilder,
    job_loss_scenario,
    medical_emergency_scenario,
    market_crash_scenario,
    lifestyle_inflation_scenario,
    side_income_scenario,
)


class TestScenarioBuilder:
    def test_basic_scenario(self):
        result = (ScenarioBuilder()
            .set_name("test")
            .set_income(base=5000, variance=0.1)
            .add_expense("rent", 1500, fixed=True)
            .add_expense("food", 600)
            .run_monte_carlo(initial_balance=10000, n_simulations=100, horizon_days=30))

        assert result.name == "test"
        assert result.runway_days_expected > 0
        assert len(result.trajectories_p50) == 31  # 30 days + initial
        assert result.expected_balance != 0

    def test_shock_scenario(self):
        from datetime import date
        result = (ScenarioBuilder()
            .set_name("shock_test")
            .set_income(base=5000)
            .add_expense("costs", 3000)
            .add_shock(date=date.today().isoformat(), amount=-10000, probability=1.0)
            .run_monte_carlo(initial_balance=15000, n_simulations=100, horizon_days=30))

        # Balance should be significantly reduced by shock
        assert result.expected_balance < 15000

    def test_zero_income(self):
        result = (ScenarioBuilder()
            .set_name("no_income")
            .set_income_multiplier(0.0)
            .set_income(base=5000)
            .add_expense("costs", 3000)
            .run_monte_carlo(initial_balance=10000, n_simulations=100, horizon_days=90))

        assert result.runway_days_expected <= 90


class TestBuiltInScenarios:
    def test_job_loss(self):
        result = job_loss_scenario(10000, 5000, 3000, unemployment_duration_days=60)
        assert result.name == "job_loss"
        assert result.runway_days_expected >= 0
        assert len(result.daily_dates) > 0

    def test_medical_emergency(self):
        result = medical_emergency_scenario(10000, 5000, 3000, emergency_cost=5000)
        assert result.name == "medical_emergency"

    def test_market_crash(self):
        result = market_crash_scenario(10000, 5000, 3000, portfolio_value=50000, crash_percentage=0.2)
        assert result.name == "market_crash"

    def test_lifestyle_inflation(self):
        result = lifestyle_inflation_scenario(10000, 5000, 3000, inflation_rate=0.15)
        assert result.name == "lifestyle_inflation"

    def test_side_income(self):
        result = side_income_scenario(10000, 5000, 3000, side_income=1000)
        assert result.name == "side_income"
        # With side income, balance should be better
        baseline = side_income_scenario(10000, 5000, 3000, side_income=0)
        assert result.expected_balance > baseline.expected_balance
