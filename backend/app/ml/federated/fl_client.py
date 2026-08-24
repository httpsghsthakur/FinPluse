"""
Finpluse v2 -- Simulated Federated Learning Client

Represents the on-device processing where raw data stays local.
Computes gradients/weights locally and returns only the updated model.
"""
import numpy as np

class FLClient:
    """Simulates local, on-device training."""

    def __init__(self, client_id: str) -> None:
        self.client_id = client_id

    def local_train(self, global_weights: list[float], local_data: np.ndarray, epochs: int = 3) -> tuple[list[float], int]:
        """Train locally on user's private data.
        
        Args:
            global_weights: Current global model from server.
            local_data: User's transaction feature matrix (staying on device).
            epochs: Local training epochs.
            
        Returns:
            Tuple of (new_local_weights, num_samples).
        """
        if len(local_data) == 0:
            return global_weights, 0

        # Simulate SGD on local data
        weights = np.array(global_weights, dtype=np.float32)
        lr = 0.01
        
        for _ in range(epochs):
            for x in local_data:
                # Dummy optimization (e.g., autoencoder reconstruction)
                pred = weights @ x
                error = pred - x.sum()  # dummy target
                grad = error * x
                weights -= lr * grad
                
        return weights.tolist(), len(local_data)
