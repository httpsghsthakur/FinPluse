"""
Finpluse v2 — Scenario Engine

Composable financial scenario builder for what-if analysis.
Supports 5 built-in scenarios and a custom DSL for user-defined scenarios.
Uses Monte Carlo simulation for probabilistic outcomes.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Expense:
    """Single expense item in a scenario."""
    name: str
    amount: float
    category: str = "general"
    is_fixed: bool = True
    elasticity: float = 1.0  # Price sensitivity for discretionary


@dataclass
class IncomeStream:
    """Income source with optional variance."""
    name: str
    amount: float
    variance: float = 0.0  # Fraction of amount (e.g. 0.1 = ±10%)


@dataclass
class Shock:
    """One-time financial shock event."""
    date: str
    amount: float
    probability: float = 1.0
    description: str = ""


@dataclass
class ScenarioConfig:
    """Complete scenario configuration."""
    name: str
    description: str = ""
    income_streams: list[IncomeStream] = field(default_factory=list)
    expenses: list[Expense] = field(default_factory=list)
    shocks: list[Shock] = field(default_factory=list)
    income_multiplier: float = 1.0
    expense_multiplier: float = 1.0
    duration_days: int = 90
    expense_adjustments: dict[str, float] = field(default_factory=dict)


@dataclass
class ScenarioResult:
    """Output of a scenario simulation."""
    name: str
    expected_balance: float
    worst_case_balance: float
    best_case_balance: float
    runway_days_expected: int
    runway_days_worst: int
    runway_days_best: int
    breakeven_date: Optional[str] = None
    trajectories_p10: list[float] = field(default_factory=list)
    trajectories_p50: list[float] = field(default_factory=list)
    trajectories_p90: list[float] = field(default_factory=list)
    daily_dates: list[str] = field(default_factory=list)


class ScenarioBuilder:
    """Fluent DSL for building custom financial scenarios.

    Usage:
        result = (ScenarioBuilder()
            .set_name("job_loss")
            .set_income(base=5000, variance=0.1)
            .add_expense("rent", 1200, fixed=True)
            .add_expense("food", 600, category="discretionary", elasticity=1.2)
            .add_shock(date="2026-09-01", amount=-5000, probability=0.1)
            .run_monte_carlo(
                initial_balance=10000,
                n_simulations=10000,
                horizon_days=90,
            ))
    """

    def __init__(self) -> None:
        self._config = ScenarioConfig(name="custom")

    def set_name(self, name: str) -> "ScenarioBuilder":
        """Set scenario name."""
        self._config.name = name
        return self

    def set_description(self, desc: str) -> "ScenarioBuilder":
        """Set scenario description."""
        self._config.description = desc
        return self

    def set_income(self, base: float, variance: float = 0.0, name: str = "primary") -> "ScenarioBuilder":
        """Set primary income stream.

        Args:
            base: Monthly base income.
            variance: Fractional variance (0.1 = ±10%).
            name: Income stream name.
        """
        self._config.income_streams.append(IncomeStream(name=name, amount=base, variance=variance))
        return self

    def set_income_multiplier(self, multiplier: float) -> "ScenarioBuilder":
        """Scale all income by a multiplier (0.0 = no income)."""
        self._config.income_multiplier = multiplier
        return self

    def add_expense(
        self,
        name: str,
        amount: float,
        fixed: bool = True,
        category: str = "general",
        elasticity: float = 1.0,
    ) -> "ScenarioBuilder":
        """Add a recurring expense.

        Args:
            name: Expense name.
            amount: Monthly amount.
            fixed: Whether this is a fixed (non-discretionary) expense.
            category: Expense category.
            elasticity: Price sensitivity for discretionary expenses.
        """
        self._config.expenses.append(Expense(
            name=name, amount=amount, category=category,
            is_fixed=fixed, elasticity=elasticity,
        ))
        return self

    def set_expense_multiplier(self, multiplier: float) -> "ScenarioBuilder":
        """Scale all expenses by a multiplier."""
        self._config.expense_multiplier = multiplier
        return self

    def add_shock(
        self, date: str, amount: float, probability: float = 1.0, description: str = ""
    ) -> "ScenarioBuilder":
        """Add a one-time financial shock.

        Args:
            date: Date string (YYYY-MM-DD).
            amount: Amount (negative for expense, positive for windfall).
            probability: Probability of occurrence (0-1).
            description: Human-readable description.
        """
        self._config.shocks.append(Shock(
            date=date, amount=amount, probability=probability, description=description,
        ))
        return self

    def add_expense_adjustment(self, category: str, multiplier: float) -> "ScenarioBuilder":
        """Adjust a specific expense category.

        Args:
            category: Category name (e.g. "rent").
            multiplier: Scale factor (1.15 = 15% increase).
        """
        self._config.expense_adjustments[category] = multiplier
        return self

    def run_monte_carlo(
        self,
        initial_balance: float,
        n_simulations: int = 10000,
        horizon_days: int = 90,
        daily_income_base: Optional[float] = None,
        daily_expense_base: Optional[float] = None,
    ) -> ScenarioResult:
        """Run Monte Carlo simulation with the configured scenario.

        Args:
            initial_balance: Starting cash balance.
            n_simulations: Number of simulation paths.
            horizon_days: Forecast horizon in days.
            daily_income_base: Override daily income (auto-computed from streams if None).
            daily_expense_base: Override daily expenses (auto-computed from expenses if None).

        Returns:
            ScenarioResult with probabilistic trajectory analysis.
        """
        rng = np.random.default_rng(42)

        # Compute daily income from streams
        if daily_income_base is not None:
            base_daily_income = daily_income_base
            income_std = base_daily_income * 0.1
        elif self._config.income_streams:
            monthly_income = sum(s.amount for s in self._config.income_streams)
            base_daily_income = monthly_income / 30.0
            avg_var = np.mean([s.variance for s in self._config.income_streams]) if self._config.income_streams else 0.1
            income_std = base_daily_income * avg_var
        else:
            base_daily_income = 200.0
            income_std = 20.0

        # Apply income multiplier
        base_daily_income *= self._config.income_multiplier

        # Compute daily expenses
        if daily_expense_base is not None:
            base_daily_expense = daily_expense_base
            expense_std = base_daily_expense * 0.15
        elif self._config.expenses:
            monthly_expense = sum(e.amount for e in self._config.expenses)
            base_daily_expense = monthly_expense / 30.0
            expense_std = base_daily_expense * 0.15
        else:
            base_daily_expense = 150.0
            expense_std = 22.0

        # Apply expense multiplier and category adjustments
        base_daily_expense *= self._config.expense_multiplier
        for cat, mult in self._config.expense_adjustments.items():
            # Simple: apply multiplier proportionally
            adjustment = base_daily_expense * (mult - 1.0) * 0.2  # Assume category is ~20% of total
            base_daily_expense += adjustment

        # Parse shock dates
        today = date.today()
        shock_days: list[tuple[int, float, float]] = []
        for shock in self._config.shocks:
            try:
                shock_date = date.fromisoformat(shock.date)
                day_offset = (shock_date - today).days
                if 0 <= day_offset < horizon_days:
                    shock_days.append((day_offset, shock.amount, shock.probability))
            except (ValueError, TypeError):
                pass

        # Run simulations
        trajectories = np.zeros((n_simulations, horizon_days + 1))
        trajectories[:, 0] = initial_balance

        for t in range(1, horizon_days + 1):
            daily_income = rng.normal(base_daily_income, max(1.0, income_std), n_simulations)
            daily_expense = rng.normal(base_daily_expense, max(1.0, expense_std), n_simulations)
            daily_income = np.maximum(daily_income, 0)
            daily_expense = np.maximum(daily_expense, 0)

            net_flow = daily_income - daily_expense

            # Apply shocks
            for shock_day, shock_amount, shock_prob in shock_days:
                if t - 1 == shock_day:
                    shock_mask = rng.random(n_simulations) < shock_prob
                    net_flow[shock_mask] += shock_amount

            trajectories[:, t] = trajectories[:, t - 1] + net_flow

        # Compute percentiles
        p10 = np.percentile(trajectories, 10, axis=0)
        p50 = np.percentile(trajectories, 50, axis=0)
        p90 = np.percentile(trajectories, 90, axis=0)

        # Compute runway (days until balance hits zero)
        def compute_runway(percentile_trajectory: np.ndarray) -> int:
            below_zero = np.where(percentile_trajectory <= 0)[0]
            return int(below_zero[0]) if len(below_zero) > 0 else horizon_days

        runway_expected = compute_runway(p50)
        runway_worst = compute_runway(p10)
        runway_best = compute_runway(p90)

        # Breakeven date
        breakeven = None
        if runway_expected < horizon_days:
            breakeven = (today + timedelta(days=runway_expected)).isoformat()

        dates = [(today + timedelta(days=d)).isoformat() for d in range(horizon_days + 1)]

        return ScenarioResult(
            name=self._config.name,
            expected_balance=float(p50[-1]),
            worst_case_balance=float(p10[-1]),
            best_case_balance=float(p90[-1]),
            runway_days_expected=runway_expected,
            runway_days_worst=runway_worst,
            runway_days_best=runway_best,
            breakeven_date=breakeven,
            trajectories_p10=p10.tolist(),
            trajectories_p50=p50.tolist(),
            trajectories_p90=p90.tolist(),
            daily_dates=dates,
        )


# ─── Built-in Scenarios ─────────────────────────────────────────

def job_loss_scenario(
    initial_balance: float,
    monthly_income: float,
    monthly_expenses: float,
    unemployment_duration_days: int = 60,
) -> ScenarioResult:
    """Simulate job loss — income drops to $0 for N days.

    Args:
        initial_balance: Current cash balance.
        monthly_income: Normal monthly income.
        monthly_expenses: Normal monthly expenses.
        unemployment_duration_days: How long without income.

    Returns:
        ScenarioResult with trajectory analysis.
    """
    return (ScenarioBuilder()
        .set_name("job_loss")
        .set_description(f"Income drops to $0 for {unemployment_duration_days} days")
        .set_income(base=monthly_income, variance=0.1)
        .set_income_multiplier(0.0)
        .add_expense("fixed_costs", monthly_expenses * 0.7, fixed=True)
        .add_expense("discretionary", monthly_expenses * 0.3, fixed=False, elasticity=0.5)
        .run_monte_carlo(initial_balance=initial_balance, horizon_days=unemployment_duration_days + 30))


def medical_emergency_scenario(
    initial_balance: float,
    monthly_income: float,
    monthly_expenses: float,
    emergency_cost: float = 5000.0,
) -> ScenarioResult:
    """Simulate a medical emergency with a large one-time expense.

    Args:
        initial_balance: Current cash balance.
        monthly_income: Normal monthly income.
        monthly_expenses: Normal monthly expenses.
        emergency_cost: One-time medical bill.

    Returns:
        ScenarioResult.
    """
    return (ScenarioBuilder()
        .set_name("medical_emergency")
        .set_description(f"One-time medical expense of ${emergency_cost:,.0f}")
        .set_income(base=monthly_income, variance=0.1)
        .add_expense("costs", monthly_expenses)
        .add_shock(date=date.today().isoformat(), amount=-emergency_cost, probability=1.0, description="Medical bill")
        .run_monte_carlo(initial_balance=initial_balance, horizon_days=90))


def market_crash_scenario(
    initial_balance: float,
    monthly_income: float,
    monthly_expenses: float,
    portfolio_value: float = 50000.0,
    crash_percentage: float = 0.20,
) -> ScenarioResult:
    """Simulate investment portfolio crash.

    Args:
        initial_balance: Current cash (not investments).
        monthly_income: Normal income.
        monthly_expenses: Normal expenses.
        portfolio_value: Total investment portfolio value.
        crash_percentage: Fraction lost (0.20 = 20% decline).

    Returns:
        ScenarioResult.
    """
    loss = portfolio_value * crash_percentage
    return (ScenarioBuilder()
        .set_name("market_crash")
        .set_description(f"Portfolio drops {crash_percentage*100:.0f}%, losing ${loss:,.0f}")
        .set_income(base=monthly_income, variance=0.15)
        .add_expense("costs", monthly_expenses)
        .add_shock(date=date.today().isoformat(), amount=-loss, probability=1.0, description="Market crash loss")
        .run_monte_carlo(initial_balance=initial_balance + portfolio_value, horizon_days=180))


def lifestyle_inflation_scenario(
    initial_balance: float,
    monthly_income: float,
    monthly_expenses: float,
    inflation_rate: float = 0.15,
) -> ScenarioResult:
    """Simulate lifestyle inflation — discretionary spending increases.

    Args:
        initial_balance: Current balance.
        monthly_income: Normal income.
        monthly_expenses: Normal expenses.
        inflation_rate: Spending increase fraction (0.15 = 15%).

    Returns:
        ScenarioResult.
    """
    return (ScenarioBuilder()
        .set_name("lifestyle_inflation")
        .set_description(f"Discretionary spending increases by {inflation_rate*100:.0f}%")
        .set_income(base=monthly_income, variance=0.1)
        .add_expense("fixed", monthly_expenses * 0.6, fixed=True)
        .add_expense("discretionary", monthly_expenses * 0.4 * (1 + inflation_rate), fixed=False)
        .run_monte_carlo(initial_balance=initial_balance, horizon_days=180))


def side_income_scenario(
    initial_balance: float,
    monthly_income: float,
    monthly_expenses: float,
    side_income: float = 1000.0,
) -> ScenarioResult:
    """Simulate adding a new side income stream.

    Args:
        initial_balance: Current balance.
        monthly_income: Primary income.
        monthly_expenses: Normal expenses.
        side_income: Additional monthly income from side work.

    Returns:
        ScenarioResult.
    """
    return (ScenarioBuilder()
        .set_name("side_income")
        .set_description(f"New side income of ${side_income:,.0f}/month")
        .set_income(base=monthly_income, variance=0.1)
        .set_income(base=side_income, variance=0.2, name="side_hustle")
        .add_expense("costs", monthly_expenses)
        .run_monte_carlo(initial_balance=initial_balance, horizon_days=180))
