"""
Gradient Boosting Regressor Model for Nonlinear RUL Prediction.
Captures complex nonlinear interactions among cumulative volume, TDS load, and flow degradation.
"""

import os
import pickle
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from typing import Dict, Any, List, Optional

from app.intelligence.feature_engineering import FEATURE_NAMES, features_dict_to_array

class GradientBoostingRULModel:
    def __init__(self, model_version: str = "gradient-boosting-v1"):
        self.model_version = model_version
        self.model = HistGradientBoostingRegressor(
            max_iter=100,
            learning_rate=0.08,
            max_depth=5,
            min_samples_leaf=10,
            random_state=42
        )
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray):
        """Fits HistGradientBoostingRegressor directly on multivariable features."""
        self.model.fit(X, y)
        self.is_fitted = True

    def predict(
        self,
        features: Dict[str, float],
        daily_consumption_lpd: float = 15.0
    ) -> Dict[str, Any]:
        """Predicts RUL in days and converts to litres."""
        if not self.is_fitted:
            raise RuntimeError("GradientBoostingRULModel must be fitted before predicting.")

        X = features_dict_to_array(features)
        raw_pred = float(self.model.predict(X)[0])
        rul_days = max(0.0, raw_pred)
        rul_litres = max(0.0, rul_days * max(0.1, daily_consumption_lpd))

        return {
            "model_version": self.model_version,
            "rul_days": round(rul_days, 1),
            "rul_litres": round(rul_litres, 1),
            "method": "Gradient Boosted Trees (Nonlinear)",
            "is_adaptive": True,
        }

    def save(self, filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as f:
            pickle.dump({"model": self.model, "version": self.model_version}, f)

    def load(self, filepath: str):
        with open(filepath, "rb") as f:
            data = pickle.load(f)
            self.model = data["model"]
            self.model_version = data.get("version", self.model_version)
            self.is_fitted = True
