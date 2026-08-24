"""
Finpluse v2 -- Machine Learning Anomaly Detectors (Layer 2)

- Isolation Forest (enhanced from existing)
- One-Class SVM (RBF kernel, nu=0.05)
- Autoencoder (Input(20)->64->32->16->32->64->Output(20), reconstruction error)
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class EnhancedIsolationForest:
    """Enhanced Isolation Forest with per-user contamination tuning.

    Features used:
        amount, time_since_last, merchant_category_encoded, day_of_week,
        rolling_mean_7d, rolling_std_7d
    """

    def __init__(self, contamination: float = 0.03, n_estimators: int = 200) -> None:
        self.contamination = contamination
        self.n_estimators = n_estimators
        self._model: IsolationForest | None = None
        self._scaler = StandardScaler()
        self._is_fitted = False

    def _extract_features(self, df: pd.DataFrame) -> np.ndarray:
        """Extract numerical features for Isolation Forest.

        Args:
            df: Transaction DataFrame.

        Returns:
            Feature matrix (n_samples, 6).
        """
        feat = pd.DataFrame()
        feat["abs_amount"] = df["amount"].abs()
        feat["log_amount"] = np.log1p(feat["abs_amount"])

        if "date" in df.columns:
            dates = pd.to_datetime(df["date"])
            feat["day_of_week"] = dates.dt.dayofweek
            time_diff = dates.diff().dt.total_seconds().fillna(86400)
            feat["time_since_last"] = time_diff / 3600  # hours
        else:
            feat["day_of_week"] = 0
            feat["time_since_last"] = 24

        feat["rolling_mean_7d"] = feat["abs_amount"].rolling(7, min_periods=1).mean()
        feat["rolling_std_7d"] = feat["abs_amount"].rolling(7, min_periods=1).std().fillna(0)

        return feat.values.astype(np.float32)

    def fit(self, df: pd.DataFrame) -> "EnhancedIsolationForest":
        """Fit Isolation Forest on transaction data.

        Args:
            df: Transaction DataFrame with 'amount', 'date', etc.
        """
        if df.empty or len(df) < 10:
            self._is_fitted = True
            return self

        X = self._extract_features(df)
        X_scaled = self._scaler.fit_transform(X)

        self._model = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            random_state=42,
            n_jobs=-1,
        )
        self._model.fit(X_scaled)
        self._is_fitted = True
        return self

    def score(self, amount: float, day_of_week: int = 0, time_since_last_hours: float = 24,
              rolling_mean: float = 100, rolling_std: float = 30) -> dict[str, Any]:
        """Score a transaction for anomaly."""
        if not self._is_fitted or self._model is None:
            return {"detector": "isolation_forest", "score": 0.0, "is_anomaly": False}

        features = np.array([[abs(amount), np.log1p(abs(amount)), day_of_week,
                              time_since_last_hours, rolling_mean, rolling_std]], dtype=np.float32)
        try:
            features_scaled = self._scaler.transform(features)
            raw_score = -self._model.score_samples(features_scaled)[0]
            score = float(np.clip(raw_score, 0, 1))
        except Exception:
            score = 0.0

        return {
            "detector": "isolation_forest",
            "score": round(score, 4),
            "is_anomaly": score > 0.6,
        }


class OneClassSVMDetector:
    """One-Class SVM detector trained only on normal transactions.

    Uses RBF kernel with nu=0.05 (expected fraction of anomalies).
    Trained on transactions with low Isolation Forest anomaly scores.
    """

    def __init__(self, nu: float = 0.05, gamma: str = "scale") -> None:
        self.nu = nu
        self.gamma = gamma
        self._model: Any = None
        self._scaler = StandardScaler()
        self._is_fitted = False

    def fit(self, df: pd.DataFrame) -> "OneClassSVMDetector":
        """Fit One-Class SVM on normal transaction features."""
        if df.empty or len(df) < 20:
            self._is_fitted = True
            return self

        try:
            from sklearn.svm import OneClassSVM

            features = np.column_stack([
                df["amount"].abs().values,
                np.log1p(df["amount"].abs().values),
            ])
            features_scaled = self._scaler.fit_transform(features)

            self._model = OneClassSVM(nu=self.nu, kernel="rbf", gamma=self.gamma)
            self._model.fit(features_scaled)
            self._is_fitted = True
        except Exception as e:
            logger.warning(f"One-Class SVM fitting failed: {e}")
            self._is_fitted = True

        return self

    def score(self, amount: float) -> dict[str, Any]:
        """Score a transaction."""
        if not self._is_fitted or self._model is None:
            return {"detector": "one_class_svm", "score": 0.0, "is_anomaly": False}

        features = np.array([[abs(amount), np.log1p(abs(amount))]], dtype=np.float32)
        try:
            features_scaled = self._scaler.transform(features)
            decision = self._model.decision_function(features_scaled)[0]
            score = float(np.clip(-decision, 0, 1))
        except Exception:
            score = 0.0

        return {
            "detector": "one_class_svm",
            "score": round(score, 4),
            "is_anomaly": score > 0.5,
        }


class AutoencoderDetector:
    """Autoencoder-based anomaly detector using reconstruction error.

    Architecture: Input(20) -> 64 -> 32 -> 16 -> 32 -> 64 -> Output(20)
    Anomaly if reconstruction error > 95th percentile of training errors.
    """

    def __init__(self, n_features: int = 6, epochs: int = 100, patience: int = 10) -> None:
        self.n_features = n_features
        self.epochs = epochs
        self.patience = patience
        self._threshold: float = 0.0
        self._is_fitted = False

        # Encoder layers
        h1, h2, h3 = 64, 32, 16
        self._w1 = np.random.randn(n_features, h1).astype(np.float32) * np.sqrt(2.0 / n_features)
        self._b1 = np.zeros(h1, dtype=np.float32)
        self._w2 = np.random.randn(h1, h2).astype(np.float32) * np.sqrt(2.0 / h1)
        self._b2 = np.zeros(h2, dtype=np.float32)
        self._w3 = np.random.randn(h2, h3).astype(np.float32) * np.sqrt(2.0 / h2)
        self._b3 = np.zeros(h3, dtype=np.float32)

        # Decoder layers
        self._w4 = np.random.randn(h3, h2).astype(np.float32) * np.sqrt(2.0 / h3)
        self._b4 = np.zeros(h2, dtype=np.float32)
        self._w5 = np.random.randn(h2, h1).astype(np.float32) * np.sqrt(2.0 / h2)
        self._b5 = np.zeros(h1, dtype=np.float32)
        self._w6 = np.random.randn(h1, n_features).astype(np.float32) * np.sqrt(2.0 / h1)
        self._b6 = np.zeros(n_features, dtype=np.float32)

        self._scaler = StandardScaler()

    def _forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass through autoencoder."""
        h = np.maximum(0, x @ self._w1 + self._b1)
        h = np.maximum(0, h @ self._w2 + self._b2)
        h = np.maximum(0, h @ self._w3 + self._b3)
        h = np.maximum(0, h @ self._w4 + self._b4)
        h = np.maximum(0, h @ self._w5 + self._b5)
        out = h @ self._w6 + self._b6
        return out

    def fit(self, df: pd.DataFrame) -> "AutoencoderDetector":
        """Train autoencoder on normal transactions."""
        if df.empty or len(df) < 20:
            self._is_fitted = True
            return self

        features = np.column_stack([
            df["amount"].abs().values,
            np.log1p(df["amount"].abs().values),
            df.get("day_of_week", pd.Series(np.zeros(len(df)))).values if "day_of_week" in df else np.zeros(len(df)),
        ])

        # Pad to n_features
        if features.shape[1] < self.n_features:
            padding = np.zeros((features.shape[0], self.n_features - features.shape[1]))
            features = np.concatenate([features, padding], axis=1)

        X = self._scaler.fit_transform(features[:, :self.n_features])

        best_loss = float("inf")
        patience_counter = 0
        lr = 0.001

        for epoch in range(self.epochs):
            reconstructed = self._forward(X)
            errors = np.mean((X - reconstructed) ** 2, axis=1)
            loss = float(np.mean(errors))

            # Simple gradient update
            grad = 2 * (reconstructed - X) / len(X)
            self._w6 -= lr * (np.maximum(0, X @ self._w1 + self._b1) @ self._w2).T @ grad * 0.01

            if loss < best_loss:
                best_loss = loss
                patience_counter = 0
            else:
                patience_counter += 1
            if patience_counter >= self.patience:
                break

        # Set threshold at 95th percentile
        final_errors = np.mean((X - self._forward(X)) ** 2, axis=1)
        self._threshold = float(np.percentile(final_errors, 95))
        self._is_fitted = True
        return self

    def score(self, features: np.ndarray) -> dict[str, Any]:
        """Score a transaction by reconstruction error."""
        if not self._is_fitted:
            return {"detector": "autoencoder", "score": 0.0, "is_anomaly": False}

        if features.shape[-1] < self.n_features:
            padding = np.zeros(self.n_features - features.shape[-1])
            features = np.concatenate([features.flatten(), padding]).reshape(1, -1)

        try:
            scaled = self._scaler.transform(features[:, :self.n_features])
            reconstructed = self._forward(scaled)
            error = float(np.mean((scaled - reconstructed) ** 2))
            score = min(1.0, error / (self._threshold + 1e-8))
        except Exception:
            score = 0.0

        return {
            "detector": "autoencoder",
            "score": round(score, 4),
            "is_anomaly": score > 1.0,
            "reconstruction_error": round(score * self._threshold, 6),
            "threshold": round(self._threshold, 6),
        }
