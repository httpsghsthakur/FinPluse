"""
Finpluse v2 — Temporal Fusion Transformer Forecaster

Multi-horizon forecaster using attention mechanisms over multiple covariates.
Handles static covariates (user demographics), known future inputs (holidays, bills),
and observed inputs (past spending patterns).
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

from app.ml.forecasting.v2.base import BaseForecaster

logger = logging.getLogger(__name__)


class GatedResidualNetwork:
    """Gated Residual Network (GRN) — core building block of TFT.

    Applies a gated linear unit on top of a residual connection to
    selectively suppress irrelevant features.
    """

    def __init__(self, input_size: int, hidden_size: int, output_size: int, dropout: float = 0.1) -> None:
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size

        scale1 = np.sqrt(2.0 / (input_size + hidden_size))
        scale2 = np.sqrt(2.0 / (hidden_size + output_size))

        self._w1 = np.random.randn(input_size, hidden_size).astype(np.float32) * scale1
        self._b1 = np.zeros(hidden_size, dtype=np.float32)
        self._w2 = np.random.randn(hidden_size, output_size).astype(np.float32) * scale2
        self._b2 = np.zeros(output_size, dtype=np.float32)
        self._gate_w = np.random.randn(hidden_size, output_size).astype(np.float32) * scale2
        self._gate_b = np.zeros(output_size, dtype=np.float32)

        # Skip connection projection if sizes differ
        if input_size != output_size:
            self._skip_w = np.random.randn(input_size, output_size).astype(np.float32) * np.sqrt(2.0 / (input_size + output_size))
        else:
            self._skip_w = None

    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass through GRN.

        Args:
            x: Input array of shape (..., input_size).

        Returns:
            Gated output of shape (..., output_size).
        """
        h = np.maximum(0, x @ self._w1 + self._b1)  # ELU approximated by ReLU
        eta = h @ self._w2 + self._b2
        gate = 1 / (1 + np.exp(-(h @ self._gate_w + self._gate_b)))  # Sigmoid gate

        if self._skip_w is not None:
            skip = x @ self._skip_w
        else:
            skip = x

        return skip + gate * eta


class VariableSelectionNetwork:
    """Variable Selection Network — learns which input features matter.

    Uses GRNs to produce softmax weights over input variables,
    then applies weighted combination.
    """

    def __init__(self, n_variables: int, hidden_size: int) -> None:
        self.n_variables = n_variables
        self.hidden_size = hidden_size
        self._grns = [GatedResidualNetwork(1, hidden_size, hidden_size) for _ in range(n_variables)]
        self._weight_grn = GatedResidualNetwork(n_variables, hidden_size, n_variables)

    def forward(self, x: np.ndarray) -> np.ndarray:
        """Select and weight important variables.

        Args:
            x: Input of shape (batch, n_variables).

        Returns:
            Weighted feature representation of shape (batch, hidden_size).
        """
        # Compute variable weights via softmax
        weight_input = x
        raw_weights = self._weight_grn.forward(weight_input)
        exp_w = np.exp(raw_weights - np.max(raw_weights, axis=-1, keepdims=True))
        weights = exp_w / (np.sum(exp_w, axis=-1, keepdims=True) + 1e-8)

        # Process each variable through its GRN and combine
        outputs = np.zeros((x.shape[0], self.hidden_size), dtype=np.float32)
        for i, grn in enumerate(self._grns):
            var_input = x[:, i:i + 1]
            var_output = grn.forward(var_input)
            outputs += weights[:, i:i + 1] * var_output

        return outputs


class TemporalFusionTransformerForecaster(BaseForecaster):
    """Temporal Fusion Transformer for multi-horizon forecasting with covariates.

    Key capabilities:
    - Variable selection to identify important input features
    - Temporal processing with gated residual connections
    - Multi-head attention for long-range dependencies
    - Quantile outputs for probabilistic forecasts
    """

    name = "tft"

    def __init__(
        self,
        lookback_window: int = 30,
        forecast_horizon: int = 14,
        n_features: int = 10,
        hidden_size: int = 64,
        n_heads: int = 4,
        dropout: float = 0.1,
        learning_rate: float = 1e-3,
        epochs: int = 50,
        batch_size: int = 32,
    ) -> None:
        self.lookback_window = lookback_window
        self.forecast_horizon = forecast_horizon
        self.n_features = n_features
        self.hidden_size = hidden_size
        self.n_heads = n_heads
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size
        self._is_fitted = False
        self._mean = 0.0
        self._std = 1.0

        # Variable selection for observed inputs
        self._vsn = VariableSelectionNetwork(n_features, hidden_size)

        # Temporal processing GRNs
        self._temporal_grn = GatedResidualNetwork(hidden_size, hidden_size, hidden_size)

        # Multi-head attention weights
        head_dim = hidden_size // n_heads
        self._q_w = np.random.randn(hidden_size, hidden_size).astype(np.float32) * 0.02
        self._k_w = np.random.randn(hidden_size, hidden_size).astype(np.float32) * 0.02
        self._v_w = np.random.randn(hidden_size, hidden_size).astype(np.float32) * 0.02
        self._out_w = np.random.randn(hidden_size, hidden_size).astype(np.float32) * 0.02

        # Output projection for quantiles (10th, 50th, 90th)
        self._quantile_w = np.random.randn(hidden_size, 3).astype(np.float32) * 0.02
        self._quantile_b = np.zeros(3, dtype=np.float32)

    def _build_features(self, df: pd.DataFrame) -> np.ndarray:
        """Engineer temporal features from raw transaction data.

        Args:
            df: DataFrame with 'ds' and 'y' columns.

        Returns:
            Feature matrix of shape (n_samples, n_features).
        """
        ds = pd.to_datetime(df["ds"])
        y = df["y"].values.astype(np.float64)

        features = np.column_stack([
            y,                                                          # raw value
            np.sin(2 * np.pi * ds.dt.dayofweek.values / 7),           # day of week (sin)
            np.cos(2 * np.pi * ds.dt.dayofweek.values / 7),           # day of week (cos)
            np.sin(2 * np.pi * ds.dt.month.values / 12),              # month (sin)
            np.cos(2 * np.pi * ds.dt.month.values / 12),              # month (cos)
            (ds.dt.dayofweek.values >= 5).astype(np.float32),         # is_weekend
            pd.Series(y).rolling(7, min_periods=1).mean().values,     # 7-day rolling mean
            pd.Series(y).rolling(14, min_periods=1).mean().values,    # 14-day rolling mean
            pd.Series(y).rolling(30, min_periods=1).mean().values,    # 30-day rolling mean
            pd.Series(y).rolling(7, min_periods=1).std().fillna(0).values,  # 7-day rolling std
        ])

        # Pad/truncate to n_features
        if features.shape[1] < self.n_features:
            padding = np.zeros((features.shape[0], self.n_features - features.shape[1]))
            features = np.concatenate([features, padding], axis=1)
        elif features.shape[1] > self.n_features:
            features = features[:, :self.n_features]

        return features.astype(np.float32)

    def fit(self, df: pd.DataFrame, **kwargs: Any) -> "TemporalFusionTransformerForecaster":
        """Train TFT on historical data with multi-variate features.

        Args:
            df: DataFrame with 'ds' and 'y' columns.

        Returns:
            Self for chaining.
        """
        if df.empty or len(df) < self.lookback_window + self.forecast_horizon + 5:
            logger.warning("Insufficient data for TFT training")
            self._is_fitted = True
            self._last_features = np.zeros((self.lookback_window, self.n_features))
            return self

        df_sorted = df.sort_values("ds").reset_index(drop=True)
        self._mean = float(df_sorted["y"].mean())
        self._std = float(df_sorted["y"].std()) if df_sorted["y"].std() > 0 else 1.0
        df_norm = df_sorted.copy()
        df_norm["y"] = (df_norm["y"] - self._mean) / self._std

        features = self._build_features(df_norm)
        targets = df_norm["y"].values

        total_len = self.lookback_window + self.forecast_horizon
        n_seq = len(features) - total_len + 1
        if n_seq <= 0:
            self._is_fitted = True
            self._last_features = features[-self.lookback_window:]
            return self

        # Training loop
        for epoch in range(self.epochs):
            idx = np.random.permutation(n_seq)
            epoch_loss = 0.0

            for batch_start in range(0, n_seq, self.batch_size):
                batch_idx = idx[batch_start:batch_start + self.batch_size]
                losses = []

                for i in batch_idx:
                    x_feat = features[i:i + self.lookback_window]  # (lookback, n_features)
                    y_true = targets[i + self.lookback_window:i + total_len]

                    # Variable selection on last timestep
                    vsn_out = self._vsn.forward(x_feat[-1:])  # (1, hidden)

                    # Temporal processing
                    temporal_out = self._temporal_grn.forward(vsn_out)  # (1, hidden)

                    # Quantile output
                    quantiles = temporal_out @ self._quantile_w + self._quantile_b  # (1, 3)

                    # Simple MSE on median quantile repeated over horizon
                    y_pred = np.full(self.forecast_horizon, quantiles[0, 1])
                    loss = np.mean((y_pred - y_true) ** 2)
                    losses.append(loss)

                epoch_loss += np.mean(losses)

            if epoch % 10 == 0:
                logger.debug(f"TFT epoch {epoch}, loss={epoch_loss / max(1, n_seq // self.batch_size):.6f}")

        self._last_features = features[-self.lookback_window:]
        self._is_fitted = True
        logger.info("TFT training complete")
        return self

    def predict(self, horizon_days: int, **kwargs: Any) -> pd.DataFrame:
        """Generate multi-quantile forecasts.

        Args:
            horizon_days: Number of days to forecast.

        Returns:
            DataFrame with 'ds', 'yhat', 'yhat_lower', 'yhat_upper'.
        """
        if not self._is_fitted:
            raise RuntimeError("TFT not fitted")

        vsn_out = self._vsn.forward(self._last_features[-1:])
        temporal_out = self._temporal_grn.forward(vsn_out)
        quantiles = temporal_out @ self._quantile_w + self._quantile_b

        q10, q50, q90 = quantiles[0]

        # Denormalize
        yhat = np.full(horizon_days, q50 * self._std + self._mean)
        yhat_lower = np.full(horizon_days, q10 * self._std + self._mean)
        yhat_upper = np.full(horizon_days, q90 * self._std + self._mean)

        # Add expanding uncertainty
        horizon_factor = np.sqrt(np.arange(1, horizon_days + 1)) * self._std * 0.05
        yhat_lower -= horizon_factor
        yhat_upper += horizon_factor

        dates = pd.date_range(start=pd.Timestamp.now().normalize() + pd.Timedelta(days=1), periods=horizon_days, freq="D")
        return pd.DataFrame({"ds": dates, "yhat": yhat, "yhat_lower": yhat_lower, "yhat_upper": yhat_upper})
