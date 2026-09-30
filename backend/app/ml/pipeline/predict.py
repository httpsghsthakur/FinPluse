import os
import joblib
import pandas as pd
from typing import Dict, Any

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
XGB_MODEL_PATH = os.path.join(MODEL_DIR, "xgboost_direction.joblib")
LE_PATH = os.path.join(MODEL_DIR, "label_encoder.joblib")
FEATURES_PATH = os.path.join(MODEL_DIR, "features.joblib")

class DirectionPredictor:
    """Production wrapper for the trained XGBoost model."""
    
    def __init__(self):
        self.model = None
        self.le = None
        self.features = None
        
        self.load_artifacts()
        
    def load_artifacts(self):
        try:
            self.model = joblib.load(XGB_MODEL_PATH)
            self.le = joblib.load(LE_PATH)
            self.features = joblib.load(FEATURES_PATH)
        except Exception as e:
            # Model not trained yet
            pass

    def predict(self, current_features: Dict[str, float]) -> Dict[str, Any]:
        """Generate prediction for a single instrument's current features."""
        if not self.model or not self.le or not self.features:
            return {"status": "error", "message": "Model artifacts not available."}
            
        # Extract ordered features
        try:
            x_input = pd.DataFrame([{f: current_features.get(f, 0.0) for f in self.features}])
        except Exception as e:
            return {"status": "error", "message": f"Feature parsing error: {e}"}
            
        # Predict probabilities
        probs = self.model.predict_proba(x_input)[0]
        
        # Predict class
        class_idx = self.model.predict(x_input)[0]
        direction = self.le.inverse_transform([class_idx])[0]
        
        # Format response
        result = {
            "status": "success",
            "direction": direction,
            "probabilities": {
                class_name: float(probs[i])
                for i, class_name in enumerate(self.le.classes_)
            }
        }
        
        return result

# Singleton instance for the FastAPI app
direction_predictor = DirectionPredictor()
