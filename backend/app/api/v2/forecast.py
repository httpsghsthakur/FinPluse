"""
Finpluse v2 -- Multi-Horizon Probabilistic Forecast API

POST /api/v2/forecast
Accepts user_id, horizon_days, confidence_levels, and optional scenarios.
Returns point forecasts with confidence intervals, runway analysis,
scenario impacts, and model metadata.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.transaction import Transaction
from app.db.models.account import Account
from app.ml.features.data_validation import ForecastRequestSchema, ForecastResponseSchema
from app.ml.forecasting.v2.base import BaseForecaster
from app.ml.forecasting.v2.prophet_forecaster import ProphetForecaster
from app.ml.forecasting.v2.nbeats_forecaster import NBeatsForecaster
from app.ml.forecasting.v2.nhits_forecaster import NHitsForecaster
from app.ml.forecasting.v2.tft_forecaster import TemporalFusionTransformerForecaster
from app.ml.forecasting.v2.ensemble import WeightedEnsemble
from app.ml.forecasting.v2.scenario_engine import (
    ScenarioBuilder,
    job_loss_scenario,
    medical_emergency_scenario,
    market_crash_scenario,
    lifestyle_inflation_scenario,
    side_income_scenario,
)
from app.ml.features.v2_features import AdvancedFeatureEngineer

logger = logging.getLogger(__name__)
router = APIRouter()

# Lazy-initialized ensemble
_ensemble: WeightedEnsemble | None = None
_feature_engineer = AdvancedFeatureEngineer()


def _get_or_create_ensemble() -> WeightedEnsemble:
    """Get or lazily initialize the forecasting ensemble."""
    global _ensemble
    if _ensemble is None:
        models: list[BaseForecaster] = [
            ProphetForecaster(),
            NBeatsForecaster(lookback_window=30, forecast_horizon=14),
            NHitsForecaster(lookback_window=60, forecast_horizon=14),
            TemporalFusionTransformerForecaster(lookback_window=30, forecast_horizon=14),
        ]
        _ensemble = WeightedEnsemble(models)
    return _ensemble


@router.post("/forecast", response_model=dict)
async def forecast_v2(
    request: ForecastRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate multi-horizon probabilistic cash flow forecast.

    Args:
        request: Forecast request with user_id, horizon, confidence levels, scenarios.
        db: Database session.

    Returns:
        Full forecast response with point forecasts, runway, scenarios, metadata.
    """
    try:
        # Fetch user transactions
        result = await db.execute(
            select(Transaction)
            .where(Transaction.user_id == request.user_id)
            .order_by(Transaction.date.asc())
        )
        transactions = result.scalars().all()

        if not transactions:
            raise HTTPException(status_code=404, detail="No transactions found for user")

        # Build DataFrame
        import pandas as pd
        tx_data = [{
            "date": t.date,
            "amount": t.amount,
            "category_id": t.category_id,
            "merchant": t.merchant,
        } for t in transactions]
        tx_df = pd.DataFrame(tx_data)

        # Feature engineering
        forecast_df = _feature_engineer.prepare_forecast_dataset(tx_df)

        if forecast_df.empty or len(forecast_df) < 14:
            raise HTTPException(status_code=400, detail="Insufficient transaction history for forecasting")

        # Get or train ensemble
        ensemble = _get_or_create_ensemble()

        try:
            ensemble.fit(forecast_df)
        except Exception as e:
            logger.warning(f"Ensemble training failed, using fallback: {e}")
            # Fallback to simple forecaster
            fallback = NBeatsForecaster(lookback_window=min(30, len(forecast_df) - 7), forecast_horizon=14)
            fallback.fit(forecast_df)
            predictions = fallback.predict(request.horizon_days)
            ensemble_weights = {"nbeats_fallback": 1.0}
            model_name = "nbeats_fallback"
        else:
            predictions = ensemble.predict(request.horizon_days)
            ensemble_weights = ensemble.get_model_weights()
            model_name = "weighted_ensemble"

        # Get current balance
        acc_result = await db.execute(
            select(Account).where(Account.user_id == request.user_id)
        )
        accounts = acc_result.scalars().all()
        current_balance = sum(a.balance for a in accounts) if accounts else 0.0

        # Build cumulative balance forecast
        point_forecasts = []
        running_balance = current_balance
        daily_burn = float(forecast_df["y"].tail(30).mean()) if len(forecast_df) >= 30 else 0

        for i, (_, row) in enumerate(predictions.iterrows()):
            daily_net = float(row["yhat"])
            running_balance += daily_net

            # Build confidence intervals
            conf_50 = None
            conf_80 = None
            conf_95 = None

            if "yhat_lower" in row and "yhat_upper" in row:
                spread = (float(row["yhat_upper"]) - float(row["yhat_lower"])) / 2
                conf_50 = (round(running_balance - spread * 0.625, 2), round(running_balance + spread * 0.625, 2))
                conf_80 = (round(running_balance - spread, 2), round(running_balance + spread, 2))
                conf_95 = (round(running_balance - spread * 1.5, 2), round(running_balance + spread * 1.5, 2))

            ds_val = row["ds"]
            if hasattr(ds_val, "strftime"):
                date_str = ds_val.strftime("%Y-%m-%d")
            else:
                date_str = str(ds_val)

            point_forecasts.append({
                "date": date_str,
                "balance": round(running_balance, 2),
                "confidence_50": conf_50,
                "confidence_80": conf_80,
                "confidence_95": conf_95,
            })

        # Compute runway
        avg_daily = abs(daily_burn) if daily_burn < 0 else 100
        runway_expected = int(current_balance / avg_daily) if avg_daily > 0 else 365
        runway_worst = max(0, int(runway_expected * 0.7))
        runway_best = min(365, int(runway_expected * 1.3))

        # Process scenarios
        scenario_impacts: dict[str, dict[str, Any]] = {}
        monthly_income = float(tx_df[tx_df["amount"] > 0]["amount"].sum() / max(1, (tx_df["date"].max() - tx_df["date"].min()).days / 30))
        monthly_expenses = float(tx_df[tx_df["amount"] < 0]["amount"].abs().sum() / max(1, (tx_df["date"].max() - tx_df["date"].min()).days / 30))

        builtin_scenarios = {
            "job_loss": lambda: job_loss_scenario(current_balance, monthly_income, monthly_expenses),
            "medical_emergency": lambda: medical_emergency_scenario(current_balance, monthly_income, monthly_expenses),
            "market_crash": lambda: market_crash_scenario(current_balance, monthly_income, monthly_expenses),
            "lifestyle_inflation": lambda: lifestyle_inflation_scenario(current_balance, monthly_income, monthly_expenses),
            "side_income": lambda: side_income_scenario(current_balance, monthly_income, monthly_expenses),
        }

        for scenario in request.scenarios:
            try:
                if scenario.name in builtin_scenarios:
                    result = builtin_scenarios[scenario.name]()
                else:
                    builder = ScenarioBuilder().set_name(scenario.name)
                    if scenario.income_multiplier != 1.0:
                        builder.set_income_multiplier(scenario.income_multiplier)
                    builder.set_income(base=monthly_income, variance=0.1)
                    builder.add_expense("total", monthly_expenses)
                    for cat, mult in scenario.expense_adjustments.items():
                        builder.add_expense_adjustment(cat, mult)
                    if scenario.one_time_amount:
                        builder.add_shock(date=date.today().isoformat(), amount=scenario.one_time_amount)
                    result = builder.run_monte_carlo(
                        initial_balance=current_balance,
                        horizon_days=scenario.duration_days,
                    )

                scenario_impacts[scenario.name] = {
                    "runway_reduction_days": max(0, runway_expected - result.runway_days_expected),
                    "breakeven_date": result.breakeven_date,
                    "expected_balance_impact": round(result.expected_balance - current_balance, 2),
                }
            except Exception as e:
                logger.warning(f"Scenario {scenario.name} failed: {e}")
                scenario_impacts[scenario.name] = {
                    "runway_reduction_days": 0,
                    "breakeven_date": None,
                    "expected_balance_impact": 0,
                }

        return {
            "point_forecasts": point_forecasts,
            "runway_days": {
                "expected": runway_expected,
                "worst_case_95": runway_worst,
                "best_case_95": runway_best,
            },
            "scenario_impacts": scenario_impacts,
            "model_metadata": {
                "primary_model": model_name,
                "mape_7d": None,
                "last_trained": None,
                "ensemble_weights": ensemble_weights,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Forecast v2 error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Forecast generation failed: {str(e)}")
