"""
Finpluse v2 -- Biometric Profiler
"""
import numpy as np

class BiometricProfiler:
    """
    Privacy-preserving biometric profiler.
    In production, this would use a Gaussian Mixture Model (GMM).
    For now, we use a simple mean/variance running update.
    """
    def __init__(self, decay_rate=0.3):
        self.decay_rate = decay_rate
        self.profiles = {} # user_id -> dict of feature stats

    def update_profile(self, user_id: str, new_features: dict[str, float]):
        """Update user profile with exponential decay."""
        if user_id not in self.profiles:
            self.profiles[user_id] = {k: {"mean": v, "var": 0.0, "count": 1} for k, v in new_features.items()}
            return
            
        profile = self.profiles[user_id]
        for k, new_val in new_features.items():
            if k not in profile:
                profile[k] = {"mean": new_val, "var": 0.0, "count": 1}
                continue
                
            old_mean = profile[k]["mean"]
            old_var = profile[k]["var"]
            count = profile[k]["count"]
            
            # Simple exponential moving average update
            alpha = self.decay_rate
            updated_mean = (1 - alpha) * old_mean + alpha * new_val
            # Approximate running variance
            updated_var = (1 - alpha) * old_var + alpha * (new_val - old_mean)**2
            
            profile[k]["mean"] = updated_mean
            profile[k]["var"] = updated_var
            profile[k]["count"] = count + 1

    def get_profile(self, user_id: str) -> dict | None:
        return self.profiles.get(user_id)
