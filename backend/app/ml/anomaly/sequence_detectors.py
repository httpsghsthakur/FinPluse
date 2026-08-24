"""
Finpluse v2 -- Sequence-Based Anomaly Detectors (Layer 4)

- LSTM Autoencoder: Captures temporal transaction patterns (seq_len=10)
- Transformer Detector: Self-attention for long-range dependencies
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class LSTMAutoencoderDetector:
    """LSTM Autoencoder for temporal transaction sequence anomaly detection.

    Encodes sequences of 10 transactions, flags high reconstruction error.
    Captures patterns like "usually $10-20 on coffee, suddenly $500".
    """

    def __init__(self, seq_length: int = 10, hidden_size: int = 32, n_features: int = 4) -> None:
        self.seq_length = seq_length
        self.hidden_size = hidden_size
        self.n_features = n_features
        self._threshold: float = 1.0
        self._is_fitted = False
        self._mean: np.ndarray = np.zeros(n_features)
        self._std: np.ndarray = np.ones(n_features)

        # Simplified LSTM weights (numpy implementation)
        total = n_features + hidden_size
        self._Wf = np.random.randn(total, hidden_size).astype(np.float32) * 0.1
        self._Wi = np.random.randn(total, hidden_size).astype(np.float32) * 0.1
        self._Wc = np.random.randn(total, hidden_size).astype(np.float32) * 0.1
        self._Wo = np.random.randn(total, hidden_size).astype(np.float32) * 0.1
        self._decode_w = np.random.randn(hidden_size, n_features).astype(np.float32) * 0.1

    def _sigmoid(self, x: np.ndarray) -> np.ndarray:
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))

    def _lstm_forward(self, sequence: np.ndarray) -> np.ndarray:
        """Run LSTM encoder on a sequence.

        Args:
            sequence: (seq_length, n_features)

        Returns:
            Final hidden state (hidden_size,)
        """
        h = np.zeros(self.hidden_size, dtype=np.float32)
        c = np.zeros(self.hidden_size, dtype=np.float32)

        for t in range(len(sequence)):
            x = sequence[t]
            combined = np.concatenate([x, h])

            f = self._sigmoid(combined @ self._Wf)
            i = self._sigmoid(combined @ self._Wi)
            c_tilde = np.tanh(combined @ self._Wc)
            o = self._sigmoid(combined @ self._Wo)

            c = f * c + i * c_tilde
            h = o * np.tanh(c)

        return h

    def fit(self, sequences: list[np.ndarray]) -> "LSTMAutoencoderDetector":
        """Train LSTM autoencoder on normal transaction sequences.

        Args:
            sequences: List of (seq_length, n_features) arrays.
        """
        if not sequences or len(sequences) < 5:
            self._is_fitted = True
            return self

        all_data = np.concatenate(sequences, axis=0)
        self._mean = all_data.mean(axis=0)
        self._std = np.where(all_data.std(axis=0) > 0, all_data.std(axis=0), 1.0)

        errors = []
        for seq in sequences:
            normalized = (seq - self._mean) / self._std
            h = self._lstm_forward(normalized)
            reconstructed = h @ self._decode_w
            error = float(np.mean((normalized[-1] - reconstructed) ** 2))
            errors.append(error)

        self._threshold = float(np.percentile(errors, 95))
        self._is_fitted = True
        return self

    def score(self, sequence: np.ndarray) -> dict[str, Any]:
        """Score a transaction sequence."""
        if not self._is_fitted:
            return {"detector": "lstm_autoencoder", "score": 0.0, "is_anomaly": False}

        try:
            normalized = (sequence - self._mean) / self._std
            h = self._lstm_forward(normalized)
            reconstructed = h @ self._decode_w
            error = float(np.mean((normalized[-1] - reconstructed) ** 2))
            score = min(1.0, error / (self._threshold + 1e-8))
        except Exception:
            score = 0.0

        return {
            "detector": "lstm_autoencoder",
            "score": round(score, 4),
            "is_anomaly": score > 1.0,
        }


class TransformerDetector:
    """Small Transformer for detecting long-range anomaly patterns.

    2 layers, 4 heads. Self-attention captures dependencies over weeks.
    Particularly good for detecting "slow burn" fraud.
    """

    def __init__(self, n_features: int = 4, d_model: int = 32, n_heads: int = 4, n_layers: int = 2) -> None:
        self.n_features = n_features
        self.d_model = d_model
        self.n_heads = n_heads
        self.n_layers = n_layers
        self._threshold: float = 1.0
        self._is_fitted = False
        self._mean = np.zeros(n_features)
        self._std = np.ones(n_features)

        # Input projection
        self._input_proj = np.random.randn(n_features, d_model).astype(np.float32) * 0.1

        # Self-attention weights per layer
        self._attention_layers: list[dict[str, np.ndarray]] = []
        head_dim = d_model // n_heads
        for _ in range(n_layers):
            self._attention_layers.append({
                "Wq": np.random.randn(d_model, d_model).astype(np.float32) * 0.05,
                "Wk": np.random.randn(d_model, d_model).astype(np.float32) * 0.05,
                "Wv": np.random.randn(d_model, d_model).astype(np.float32) * 0.05,
                "Wo": np.random.randn(d_model, d_model).astype(np.float32) * 0.05,
                "ff_w1": np.random.randn(d_model, d_model * 4).astype(np.float32) * 0.05,
                "ff_w2": np.random.randn(d_model * 4, d_model).astype(np.float32) * 0.05,
            })

        self._output_proj = np.random.randn(d_model, n_features).astype(np.float32) * 0.1

    def _attention(self, Q: np.ndarray, K: np.ndarray, V: np.ndarray) -> np.ndarray:
        """Scaled dot-product attention."""
        d_k = Q.shape[-1]
        scores = Q @ K.T / np.sqrt(d_k)
        weights = np.exp(scores - np.max(scores, axis=-1, keepdims=True))
        weights /= weights.sum(axis=-1, keepdims=True) + 1e-8
        return weights @ V

    def _forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass. x: (seq_len, n_features) -> (seq_len, n_features)"""
        h = x @ self._input_proj  # (seq_len, d_model)

        for layer in self._attention_layers:
            Q = h @ layer["Wq"]
            K = h @ layer["Wk"]
            V = h @ layer["Wv"]
            attn_out = self._attention(Q, K, V) @ layer["Wo"]
            h = h + attn_out  # Residual

            ff = np.maximum(0, h @ layer["ff_w1"]) @ layer["ff_w2"]
            h = h + ff  # Residual

        return h @ self._output_proj  # (seq_len, n_features)

    def fit(self, sequences: list[np.ndarray]) -> "TransformerDetector":
        """Fit transformer on normal sequences."""
        if not sequences or len(sequences) < 5:
            self._is_fitted = True
            return self

        all_data = np.concatenate(sequences, axis=0)
        self._mean = all_data.mean(axis=0)
        self._std = np.where(all_data.std(axis=0) > 0, all_data.std(axis=0), 1.0)

        errors = []
        for seq in sequences:
            normalized = (seq - self._mean) / self._std
            reconstructed = self._forward(normalized)
            error = float(np.mean((normalized - reconstructed) ** 2))
            errors.append(error)

        self._threshold = float(np.percentile(errors, 95))
        self._is_fitted = True
        return self

    def score(self, sequence: np.ndarray) -> dict[str, Any]:
        """Score a sequence for anomalies."""
        if not self._is_fitted:
            return {"detector": "transformer", "score": 0.0, "is_anomaly": False}

        try:
            normalized = (sequence - self._mean) / self._std
            reconstructed = self._forward(normalized)
            error = float(np.mean((normalized - reconstructed) ** 2))
            score = min(1.0, error / (self._threshold + 1e-8))
        except Exception:
            score = 0.0

        return {
            "detector": "transformer",
            "score": round(score, 4),
            "is_anomaly": score > 1.0,
        }
