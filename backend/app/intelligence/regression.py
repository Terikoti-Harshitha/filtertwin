"""
Multivariable Linear Regression Model for RUL Prediction.
Uses standardized multivariable operational features and computes coefficient contributions
for diagnostic explainability.
"""

import os
import pickle
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from typing import Dict, Any, List, Optional, Tuple

from app.intelligence.feature_engineering import FEATURE_NAMES, features_dict_to_array

class LinearRegressionRULModel:
    def __init__(self, model_version: str = "linear-regression-v1"):
        self.model_version = model_version
        self.scaler = StandardScaler()
        self.model = Ridge(alpha=1.0)
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray):
        """Fits scaler and Ridge linear regression model on training data."""
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_fitted = True

    def predict(
        self,
        features: Dict[str, float],
        daily_consumption_lpd: float = 15.0
    ) -> Dict[str, Any]:
        """
        Predicts RUL in days and converts to litres.
        Also calculates standardized feature contributions.
        """
        if not self.is_fitted:
            raise RuntimeError("LinearRegressionRULModel must be fitted before predicting.")

        X = features_dict_to_array(features)
        X_scaled = self.scaler.transform(X)

        raw_pred = float(self.model.predict(X_scaled)[0])
        rul_days = max(0.0, raw_pred)
        rul_litres = max(0.0, rul_days * max(0.1, daily_consumption_lpd))

        # Explainability: feature contributions = coef_i * scaled_x_i
        coefs = self.model.coef_
        contributions = {}
        for i, name in enumerate(FEATURE_NAMES):
            impact = float(coefs[i] * X_scaled[0, i])
            contributions[name] = impact

        return {
            "model_version": self.model_version,
            "rul_days": round(rul_days, 1),
            "rul_litres": round(rul_litres, 1),
            "method": "Multivariable Linear Regression",
            "is_adaptive": True,
            "feature_contributions": contributions,
        }

    def save(self, filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as f:
            pickle.dump({"model": self.model, "scaler": self.scaler, "version": self.model_version}, f)

    def load(self, filepath: str):
        with open(filepath, "rb") as f:
            data = pickle.load(f)
            self.model = data["model"]
            self.scaler = data["scaler"]
            self.model_version = data.get("version", self.model_version)
            self.is_fitted = True
