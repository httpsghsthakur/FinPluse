"""
Finpluse v2 -- Advanced Feature Engineering for Forecasting

Computes lag features, calendar features, cyclical encodings,
category-wise spending velocity, income stability score,
and Fourier-based recurring bill detection.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class AdvancedFeatureEngineer:
    """Computes all v2 features from raw transaction history.

    Features produced:
        Lag: 1d, 7d, 14d, 30d rolling means of daily net spending
        Calendar: day_of_week, is_weekend, is_holiday (US federal)
        Cyclical: sin/cos encodings of month and day_of_week
        Category: spending velocity per category (7-day trend slope)
        Stability: income stability score (CV of income over 90 days)
        Recurring: Fourier-detected periodicity in expense patterns
    """

    # US Federal holidays (month, day) -- fixed-date only for simplicity
    US_HOLIDAYS: set[tuple[int, int]] = {
        (1, 1), (7, 4), (11, 11), (12, 25),
    }

    def compute_daily_features(self, transactions_df: pd.DataFrame) -> pd.DataFrame:
        """Transform raw transactions into daily feature vectors.

        Args:
            transactions_df: Raw transactions with 'date', 'amount', 'category_id', 'merchant'.

        Returns:
            DataFrame indexed by date with all engineered features.
        """
        if transactions_df.empty:
            return pd.DataFrame()

        df = transactions_df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df["date"]):
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])
        df["date"] = df["date"].dt.normalize()

        # Aggregate to daily net amount
        daily = df.groupby("date").agg(
            daily_net=("amount", "sum"),
            n_transactions=("amount", "count"),
            daily_spend=("amount", lambda x: x[x < 0].sum()),
            daily_income=("amount", lambda x: x[x > 0].sum()),
        ).sort_index()

        # Fill missing dates
        full_range = pd.date_range(start=daily.index.min(), end=daily.index.max(), freq="D")
        daily = daily.reindex(full_range, fill_value=0.0)
        daily.index.name = "date"

        # === Lag Features ===
        for window in [1, 7, 14, 30]:
            daily[f"rolling_mean_{window}d"] = daily["daily_net"].rolling(window, min_periods=1).mean()
            daily[f"rolling_std_{window}d"] = daily["daily_net"].rolling(window, min_periods=1).std().fillna(0)

        # === Calendar Features ===
        daily["day_of_week"] = daily.index.dayofweek
        daily["day_of_month"] = daily.index.day
        daily["month"] = daily.index.month
        daily["is_weekend"] = (daily.index.dayofweek >= 5).astype(int)
        daily["is_month_start"] = (daily.index.day == 1).astype(int)
        daily["is_month_end"] = (daily.index.day == daily.index.days_in_month).astype(int)
        daily["is_holiday"] = daily.index.map(
            lambda d: 1 if (d.month, d.day) in self.US_HOLIDAYS else 0
        )
        # Payday indicators (1st and 15th are common paydays)
        daily["is_payday"] = daily.index.day.isin([1, 15]).astype(int)

        # === Cyclical Encodings ===
        daily["dow_sin"] = np.sin(2 * np.pi * daily["day_of_week"] / 7)
        daily["dow_cos"] = np.cos(2 * np.pi * daily["day_of_week"] / 7)
        daily["month_sin"] = np.sin(2 * np.pi * daily["month"] / 12)
        daily["month_cos"] = np.cos(2 * np.pi * daily["month"] / 12)
        daily["dom_sin"] = np.sin(2 * np.pi * daily["day_of_month"] / 31)
        daily["dom_cos"] = np.cos(2 * np.pi * daily["day_of_month"] / 31)

        return daily

    def compute_category_velocity(self, transactions_df: pd.DataFrame) -> dict[str, float]:
        """Compute spending velocity (7-day trend slope) per category.

        Args:
            transactions_df: Transactions with 'date', 'amount', 'category_id'.

        Returns:
            Dict mapping category_id to velocity (positive = increasing spend).
        """
        if transactions_df.empty:
            return {}

        df = transactions_df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df["date"]):
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # Last 30 days only
        cutoff = df["date"].max() - pd.Timedelta(days=30)
        recent = df[df["date"] >= cutoff].copy()
        if recent.empty:
            return {}

        recent["week"] = recent["date"].dt.isocalendar().week.astype(int)
        velocities: dict[str, float] = {}

        for cat_id, group in recent.groupby("category_id"):
            weekly_spend = group.groupby("week")["amount"].sum().abs()
            if len(weekly_spend) < 2:
                velocities[str(cat_id)] = 0.0
                continue
            # Simple linear regression slope
            x = np.arange(len(weekly_spend), dtype=np.float64)
            y = weekly_spend.values.astype(np.float64)
            slope = float(np.polyfit(x, y, 1)[0])
            velocities[str(cat_id)] = round(slope, 2)

        return velocities

    def compute_income_stability_score(self, transactions_df: pd.DataFrame, window_days: int = 90) -> float:
        """Compute income stability as inverse of coefficient of variation.

        A score of 1.0 means perfectly stable income; lower means more volatile.

        Args:
            transactions_df: Transactions with 'date' and 'amount'.
            window_days: Number of days to look back.

        Returns:
            Stability score between 0 and 1.
        """
        if transactions_df.empty:
            return 0.0

        df = transactions_df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df["date"]):
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        cutoff = df["date"].max() - pd.Timedelta(days=window_days)
        income = df[(df["date"] >= cutoff) & (df["amount"] > 0)]

        if income.empty:
            return 0.0

        # Monthly income aggregation
        income["month"] = income["date"].dt.to_period("M")
        monthly = income.groupby("month")["amount"].sum()

        if len(monthly) < 2:
            return 0.8  # Insufficient data, assume moderate stability

        cv = float(monthly.std() / monthly.mean()) if monthly.mean() > 0 else 1.0
        # Convert CV to 0-1 score (lower CV = higher stability)
        stability = max(0.0, min(1.0, 1.0 - cv))
        return round(stability, 3)

    def detect_recurring_expenses_fourier(self, transactions_df: pd.DataFrame) -> list[dict[str, Any]]:
        """Detect periodic expense patterns using Fourier analysis.

        Applies FFT to per-merchant spending time series to find
        dominant frequencies indicating weekly, biweekly, or monthly patterns.

        Args:
            transactions_df: Transactions with 'date', 'amount', 'merchant'.

        Returns:
            List of detected recurring patterns with merchant, period, and confidence.
        """
        if transactions_df.empty:
            return []

        df = transactions_df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df["date"]):
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # Only expenses
        expenses = df[df["amount"] < 0].copy()
        if expenses.empty:
            return []

        results: list[dict[str, Any]] = []
        min_occurrences = 3

        for merchant, group in expenses.groupby("merchant"):
            if len(group) < min_occurrences:
                continue

            # Create daily indicator: 1 on days with this merchant, 0 otherwise
            date_range = pd.date_range(group["date"].min(), group["date"].max(), freq="D")
            if len(date_range) < 14:
                continue

            indicator = pd.Series(0, index=date_range)
            for d in group["date"]:
                if d in indicator.index:
                    indicator[d] = 1

            # FFT
            signal = indicator.values.astype(np.float64)
            n = len(signal)
            if n < 14:
                continue

            fft_vals = np.fft.rfft(signal)
            magnitudes = np.abs(fft_vals)
            freqs = np.fft.rfftfreq(n, d=1.0)  # Frequencies in cycles/day

            # Skip DC component
            if len(magnitudes) < 3:
                continue
            magnitudes[0] = 0

            # Find dominant frequency
            peak_idx = np.argmax(magnitudes[1:]) + 1
            if magnitudes[peak_idx] < 1.5:  # Minimum magnitude threshold
                continue

            peak_freq = freqs[peak_idx]
            if peak_freq > 0:
                period_days = 1.0 / peak_freq
            else:
                continue

            # Classify period
            if 6 <= period_days <= 8:
                freq_label = "weekly"
            elif 13 <= period_days <= 16:
                freq_label = "biweekly"
            elif 28 <= period_days <= 32:
                freq_label = "monthly"
            elif 58 <= period_days <= 62:
                freq_label = "bimonthly"
            elif 85 <= period_days <= 95:
                freq_label = "quarterly"
            else:
                freq_label = f"every_{int(period_days)}_days"

            # Confidence based on magnitude relative to noise floor
            noise_floor = np.mean(magnitudes[1:])
            confidence = min(1.0, float(magnitudes[peak_idx] / (noise_floor + 1e-6)) / 10.0)

            avg_amount = float(group["amount"].mean())

            results.append({
                "merchant": str(merchant),
                "period_days": round(period_days, 1),
                "frequency": freq_label,
                "confidence": round(confidence, 3),
                "avg_amount": round(avg_amount, 2),
                "occurrences": len(group),
            })

        # Sort by confidence descending
        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results

    def prepare_forecast_dataset(self, transactions_df: pd.DataFrame) -> pd.DataFrame:
        """Prepare a complete feature-rich dataset for model training.

        Combines all feature types into a single DataFrame ready for
        forecasting model consumption.

        Args:
            transactions_df: Raw transactions.

        Returns:
            DataFrame with 'ds' (date) and 'y' (daily net) plus all features.
        """
        daily = self.compute_daily_features(transactions_df)
        if daily.empty:
            return pd.DataFrame(columns=["ds", "y"])

        result = daily.reset_index()
        result = result.rename(columns={"date": "ds", "daily_net": "y"})
        return result
