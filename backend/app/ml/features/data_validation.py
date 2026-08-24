"""
Finpluse v2 -- Data Validation for Forecasting Pipeline

Pydantic models for all forecasting I/O schemas plus data quality checks
for anomaly flagging, distribution shift detection, and missing value handling.
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Optional

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


# === Pydantic Schemas ===

class ScenarioInput(BaseModel):
    """Single scenario definition for forecast request."""
    name: str = Field(..., description="Scenario identifier")
    income_multiplier: float = Field(1.0, ge=0.0, le=10.0)
    duration_days: int = Field(90, ge=1, le=365)
    expense_adjustments: dict[str, float] = Field(default_factory=dict)
    one_time_amount: Optional[float] = None

class ForecastRequestSchema(BaseModel):
    """v2 Forecast API request schema."""
    user_id: str = Field(..., min_length=1)
    horizon_days: int = Field(90, ge=1, le=365)
    confidence_levels: list[float] = Field(default_factory=lambda: [0.5, 0.8, 0.95])
    scenarios: list[ScenarioInput] = Field(default_factory=list)

    @field_validator("confidence_levels")
    @classmethod
    def validate_confidence_levels(cls, v: list[float]) -> list[float]:
        for level in v:
            if not 0 < level < 1:
                raise ValueError(f"Confidence level {level} must be between 0 and 1")
        return sorted(v)

class ForecastPointSchema(BaseModel):
    """Single forecast point output."""
    date: str
    balance: float
    confidence_50: Optional[tuple[float, float]] = None
    confidence_80: Optional[tuple[float, float]] = None
    confidence_95: Optional[tuple[float, float]] = None

class RunwaySchema(BaseModel):
    """Runway analysis output."""
    expected: int
    worst_case_95: int
    best_case_95: int

class ScenarioImpactSchema(BaseModel):
    """Impact of a single scenario."""
    runway_reduction_days: int
    breakeven_date: Optional[str] = None
    expected_balance_impact: float = 0.0

class ModelMetadataSchema(BaseModel):
    """Model metadata for transparency."""
    primary_model: str
    mape_7d: Optional[float] = None
    last_trained: Optional[str] = None
    ensemble_weights: dict[str, float] = Field(default_factory=dict)

class ForecastResponseSchema(BaseModel):
    """v2 Forecast API response schema."""
    point_forecasts: list[ForecastPointSchema]
    runway_days: RunwaySchema
    scenario_impacts: dict[str, ScenarioImpactSchema] = Field(default_factory=dict)
    model_metadata: ModelMetadataSchema


# === Data Quality Checks ===

class DataQualityChecker:
    """Validates transaction data before model training.

    Checks performed:
        - Missing values in required columns
        - Date range validity
        - Amount distribution anomalies in training data
        - Duplicate detection
        - Distribution shift via KS test
    """

    REQUIRED_COLUMNS = {"date", "amount"}

    def validate(self, df: pd.DataFrame) -> dict[str, Any]:
        """Run all quality checks on a transaction DataFrame.

        Args:
            df: Raw transaction data.

        Returns:
            Dict with 'is_valid', 'warnings', 'errors', and 'stats'.
        """
        errors: list[str] = []
        warnings: list[str] = []
        stats: dict[str, Any] = {}

        if df.empty:
            return {"is_valid": False, "errors": ["DataFrame is empty"], "warnings": [], "stats": {}}

        # Check required columns
        missing_cols = self.REQUIRED_COLUMNS - set(df.columns)
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
            return {"is_valid": False, "errors": errors, "warnings": warnings, "stats": stats}

        # Missing values
        null_counts = df[list(self.REQUIRED_COLUMNS)].isnull().sum()
        for col, count in null_counts.items():
            if count > 0:
                pct = count / len(df) * 100
                if pct > 20:
                    errors.append(f"Column '{col}' has {pct:.1f}% missing values")
                elif pct > 5:
                    warnings.append(f"Column '{col}' has {pct:.1f}% missing values")

        # Date range
        try:
            dates = pd.to_datetime(df["date"])
            date_range = (dates.max() - dates.min()).days
            stats["date_range_days"] = date_range
            stats["n_transactions"] = len(df)
            if date_range < 14:
                warnings.append(f"Only {date_range} days of data -- forecasts may be unreliable")
        except Exception:
            errors.append("Could not parse date column")

        # Amount distribution
        amounts = df["amount"].dropna()
        if len(amounts) > 0:
            stats["amount_mean"] = float(amounts.mean())
            stats["amount_std"] = float(amounts.std())
            stats["amount_min"] = float(amounts.min())
            stats["amount_max"] = float(amounts.max())

            # Flag extreme outliers in training data (|z| > 5)
            z_scores = np.abs((amounts - amounts.mean()) / (amounts.std() + 1e-8))
            n_extreme = int((z_scores > 5).sum())
            if n_extreme > 0:
                warnings.append(f"{n_extreme} extreme outliers detected (|z|>5) in training data")
                stats["n_extreme_outliers"] = n_extreme

        # Duplicates
        if "merchant" in df.columns:
            n_dupes = df.duplicated(subset=["date", "amount", "merchant"]).sum()
            if n_dupes > 0:
                warnings.append(f"{n_dupes} potential duplicate transactions detected")

        is_valid = len(errors) == 0
        return {"is_valid": is_valid, "errors": errors, "warnings": warnings, "stats": stats}

    def detect_distribution_shift(
        self,
        reference_df: pd.DataFrame,
        current_df: pd.DataFrame,
        columns: list[str] | None = None,
        p_threshold: float = 0.05,
    ) -> dict[str, Any]:
        """Detect distribution shift using Kolmogorov-Smirnov test.

        Args:
            reference_df: Historical reference data.
            current_df: Recent data to compare.
            columns: Columns to test (defaults to ['amount']).
            p_threshold: P-value threshold for declaring shift.

        Returns:
            Dict with 'has_drift', 'drifted_features', and per-feature results.
        """
        from scipy import stats as sp_stats

        if columns is None:
            columns = ["amount"]

        results: dict[str, Any] = {"has_drift": False, "drifted_features": [], "details": {}}

        for col in columns:
            if col not in reference_df.columns or col not in current_df.columns:
                continue

            ref_values = reference_df[col].dropna().values
            cur_values = current_df[col].dropna().values

            if len(ref_values) < 5 or len(cur_values) < 5:
                continue

            try:
                ks_stat, p_value = sp_stats.ks_2samp(ref_values, cur_values)
                has_drift = p_value < p_threshold

                results["details"][col] = {
                    "ks_statistic": round(float(ks_stat), 4),
                    "p_value": round(float(p_value), 6),
                    "has_drift": has_drift,
                    "ref_mean": round(float(np.mean(ref_values)), 2),
                    "cur_mean": round(float(np.mean(cur_values)), 2),
                }

                if has_drift:
                    results["has_drift"] = True
                    results["drifted_features"].append(col)
            except Exception as e:
                logger.warning(f"KS test failed for {col}: {e}")

        return results
