"""
Finpluse v2 -- Federated Learning Aggregation Server
"""
import logging
import numpy as np
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class FLServer:
    def __init__(self, global_model_dim=5):
        self.global_weights = [0.0] * global_model_dim
        self.collected_updates = []
        self.min_clients = 10
        
    def submit_update(self, client_id: str, weights: List[float], n_samples: int):
        self.collected_updates.append({"weights": weights, "n_samples": n_samples})
        
    def aggregate(self):
        if len(self.collected_updates) < self.min_clients:
            return {"status": "waiting"}
            
        total_samples = sum(u["n_samples"] for u in self.collected_updates)
        new_weights = np.zeros(len(self.global_weights))
        
        for u in self.collected_updates:
            weight = u["n_samples"] / total_samples
            new_weights += np.array(u["weights"]) * weight
            
        self.global_weights = new_weights.tolist()
        self.collected_updates = []
        return {"status": "success"}
        
    def get_global_model(self) -> List[float]:
        return self.global_weights
