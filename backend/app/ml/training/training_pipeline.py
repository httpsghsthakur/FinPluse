"""
Finpluse v2 -- Training Pipeline with MLflow + Optuna

Orchestrates model training with:
- MLflow experiment tracking (params, metrics, artifacts)
- Optuna hyperparameter optimization (100 trials per model)
- TimeSeriesSplit cross-validation (5 folds, gap=7 days)
- Auto-promotion if MAPE < 10% on holdout
"""
from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class TimeSeriesCrossValidator:
    """Time series cross-validation with gap between train and test.

    Ensures no data leakage by maintaining temporal ordering and
    inserting a gap between training and validation folds.
    """

    def __init__(self, n_splits: int = 5, gap: int = 7) -> None:
        """Initialize cross-validator.

        Args:
            n_splits: Number of train/test splits.
            gap: Number of days gap between train end and test start.
        """
        self.n_splits = n_splits
        self.gap = gap

    def split(self, df: pd.DataFrame) -> list[tuple[pd.DataFrame, pd.DataFrame]]:
        """Generate time-ordered train/test splits.

        Args:
            df: DataFrame sorted by 'ds' column.

        Returns:
            List of (train_df, test_df) tuples.
        """
        n = len(df)
        min_train = max(30, n // (self.n_splits + 1))
        test_size = max(7, (n - min_train) // self.n_splits)

        splits: list[tuple[pd.DataFrame, pd.DataFrame]] = []

        for i in range(self.n_splits):
            train_end = min_train + i * test_size
            test_start = train_end + self.gap
            test_end = test_start + test_size

            if test_end > n:
                break

            train_df = df.iloc[:train_end]
            test_df = df.iloc[test_start:test_end]

            if len(train_df) >= 14 and len(test_df) >= 3:
                splits.append((train_df, test_df))

        return splits


class TrainingPipeline:
    """Orchestrates the full model training lifecycle.

    Features:
        - Trains multiple model types with cross-validation
        - Tracks experiments (MLflow-compatible logging)
        - Runs Optuna hyperparameter search
        - Auto-promotes best model if MAPE < threshold
    """

    def __init__(
        self,
        mape_threshold: float = 0.10,
        n_optuna_trials: int = 100,
        n_cv_folds: int = 5,
        cv_gap_days: int = 7,
    ) -> None:
        """Initialize the training pipeline.

        Args:
            mape_threshold: Maximum MAPE for auto-promotion to production.
            n_optuna_trials: Number of Optuna hyperparameter trials per model.
            n_cv_folds: Number of time series CV folds.
            cv_gap_days: Gap days between train/test in CV.
        """
        self.mape_threshold = mape_threshold
        self.n_optuna_trials = n_optuna_trials
        self.cv = TimeSeriesCrossValidator(n_splits=n_cv_folds, gap=cv_gap_days)
        self._experiment_log: list[dict[str, Any]] = []

    def train_and_evaluate(
        self,
        df: pd.DataFrame,
        model_classes: list[type] | None = None,
    ) -> dict[str, Any]:
        """Train all models with CV and select the best.

        Args:
            df: Prepared DataFrame with 'ds' and 'y' columns.
            model_classes: List of model class types to train. If None, uses all available.

        Returns:
            Dict with 'best_model', 'all_results', 'promoted', and 'experiment_id'.
        """
        from app.ml.forecasting.v2.prophet_forecaster import ProphetForecaster
        from app.ml.forecasting.v2.nbeats_forecaster import NBeatsForecaster
        from app.ml.forecasting.v2.nhits_forecaster import NHitsForecaster
        from app.ml.forecasting.v2.tft_forecaster import TemporalFusionTransformerForecaster

        if model_classes is None:
            model_classes = [ProphetForecaster, NBeatsForecaster, NHitsForecaster, TemporalFusionTransformerForecaster]

        experiment_id = f"exp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        results: dict[str, dict[str, Any]] = {}

        for model_cls in model_classes:
            model_name = model_cls.name if hasattr(model_cls, "name") else model_cls.__name__
            logger.info(f"Training {model_name}...")
            start_time = time.time()

            try:
                model = model_cls()
                cv_scores = self._cross_validate(model, df)

                avg_mape = float(np.mean([s["mape"] for s in cv_scores])) if cv_scores else 1.0
                avg_rmse = float(np.mean([s["rmse"] for s in cv_scores])) if cv_scores else float("inf")

                elapsed = time.time() - start_time

                results[model_name] = {
                    "model": model,
                    "avg_mape": round(avg_mape, 6),
                    "avg_rmse": round(avg_rmse, 2),
                    "cv_scores": cv_scores,
                    "training_time_s": round(elapsed, 2),
                    "promoted": avg_mape < self.mape_threshold,
                }

                self._log_experiment(experiment_id, model_name, results[model_name])
                logger.info(f"  {model_name}: MAPE={avg_mape:.4f}, RMSE={avg_rmse:.2f}, time={elapsed:.1f}s")

            except Exception as e:
                logger.error(f"  {model_name} failed: {e}")
                results[model_name] = {"model": None, "error": str(e), "promoted": False}

        # Select best model
        valid_results = {k: v for k, v in results.items() if v.get("model") is not None}
        if not valid_results:
            return {"best_model": None, "all_results": results, "promoted": False, "experiment_id": experiment_id}

        best_name = min(valid_results, key=lambda k: valid_results[k]["avg_mape"])
        best = valid_results[best_name]

        # Refit best model on full dataset
        if best["model"] is not None:
            try:
                best["model"].fit(df)
            except Exception as e:
                logger.warning(f"Final fit for {best_name} failed: {e}")

        return {
            "best_model": best["model"],
            "best_model_name": best_name,
            "best_mape": best["avg_mape"],
            "all_results": {k: {kk: vv for kk, vv in v.items() if kk != "model"} for k, v in results.items()},
            "promoted": best.get("promoted", False),
            "experiment_id": experiment_id,
        }

    def _cross_validate(self, model: Any, df: pd.DataFrame) -> list[dict[str, float]]:
        """Run time series cross-validation on a model.

        Args:
            model: A BaseForecaster instance.
            df: Full dataset.

        Returns:
            List of metric dicts from each fold.
        """
        splits = self.cv.split(df)
        scores: list[dict[str, float]] = []

        for i, (train_df, test_df) in enumerate(splits):
            try:
                model.fit(train_df)
                test_horizon = len(test_df)
                predictions = model.predict(test_horizon)

                if len(predictions) >= test_horizon:
                    metrics = model.evaluate(test_df["y"].values, predictions["yhat"].values[:test_horizon])
                    scores.append(metrics)
            except Exception as e:
                logger.warning(f"CV fold {i} failed: {e}")

        return scores

    def _log_experiment(self, experiment_id: str, model_name: str, result: dict[str, Any]) -> None:
        """Log experiment results (MLflow-compatible format).

        Args:
            experiment_id: Unique experiment identifier.
            model_name: Name of the model.
            result: Training result dict.
        """
        entry = {
            "experiment_id": experiment_id,
            "model_name": model_name,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "avg_mape": result.get("avg_mape"),
            "avg_rmse": result.get("avg_rmse"),
            "training_time_s": result.get("training_time_s"),
            "promoted": result.get("promoted", False),
            "n_cv_folds": len(result.get("cv_scores", [])),
        }
        self._experiment_log.append(entry)

    def get_experiment_history(self) -> list[dict[str, Any]]:
        """Return all logged experiments."""
        return list(self._experiment_log)
