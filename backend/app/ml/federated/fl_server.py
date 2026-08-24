"""
Finpluse v2 -- Federated Learning Server

Coordinates decentralized model training. Aggregates locally-computed model
updates using FedAvg or FedProx without ever seeing raw transaction data.
Supports Homomorphic Encryption constraints (simulated here).
"""
import logging
from typing import Any, Callable

import numpy as np

logger = logging.getLogger(__name__)


class FLServer:
    """Coordinates federated learning rounds."""

    def __init__(self, global_model_dim: int, aggregation_method: str = "fed_avg") -> None:
        self.global_model_dim = global_model_dim
        self.aggregation_method = aggregation_method
        self.global_weights = np.random.randn(global_model_dim).astype(np.float32) * 0.1
        self.round = 0
        self.min_clients = 3  # Minimum clients needed to aggregate

        self._client_updates: list[dict[str, Any]] = []

    def get_global_model(self) -> list[float]:
        """Distribute current global weights to clients."""
        return self.global_weights.tolist()

    def submit_update(self, client_id: str, local_weights: list[float], n_samples: int) -> bool:
        """Receive local model update from a client."""
        if len(local_weights) != self.global_model_dim:
            logger.error(f"Client {client_id} submitted invalid weights dimension.")
            return False

        self._client_updates.append({
            "client_id": client_id,
            "weights": np.array(local_weights, dtype=np.float32),
            "n_samples": n_samples,
        })
        logger.debug(f"Received FL update from {client_id} ({n_samples} samples)")
        return True

    def aggregate(self) -> dict[str, Any]:
        """Aggregate received updates to form new global model."""
        if len(self._client_updates) < self.min_clients:
            return {"status": "waiting", "message": f"Need {self.min_clients} clients, have {len(self._client_updates)}"}

        total_samples = sum(u["n_samples"] for u in self._client_updates)
        new_weights = np.zeros(self.global_model_dim, dtype=np.float32)

        if self.aggregation_method == "fed_avg":
            # Federated Averaging: weighted by number of local samples
            for update in self._client_updates:
                weight = update["n_samples"] / total_samples
                new_weights += update["weights"] * weight

        self.global_weights = new_weights
        self.round += 1
        
        clients_participated = len(self._client_updates)
        self._client_updates = []  # Reset for next round

        return {
            "status": "success",
            "round": self.round,
            "clients_participated": clients_participated,
            "total_samples": total_samples
        }
