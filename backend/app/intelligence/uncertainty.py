"""
Uncertainty Estimation Engine using Quantile Regression.
Trains quantile regressors for 10th, 50th (median), and 90th percentiles to produce
an 80% empirical prediction interval [Q_0.10, Q_0.90].
Calculates Prediction Interval Coverage Probability (PICP) and Average Interval Width.
"""

import os
import pickle
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from typing import Dict, Any, List, Optional, Tuple

from app.intelligence.feature_engineering import FEATURE_NAMES, features_dict_to_array

class QuantileUncertaintyEngine:
    def __init__(self, model_version: str = "quantile-regressor-v1"):
        self.model_version = model_version
        # Models for 10th percentile, median (50th), and 90th percentile
        self.q10_model = HistGradientBoostingRegressor(
            loss="quantile", quantile=0.10, max_iter=80, learning_rate=0.08, random_state=42
        )
        self.q50_model = HistGradientBoostingRegressor(
            loss="quantile", quantile=0.50, max_iter=80, learning_rate=0.08, random_state=42
        )
        self.q90_model = HistGradientBoostingRegressor(
            loss="quantile", quantile=0.90, max_iter=80, learning_rate=0.08, random_state=42
        )
        self.is_fitted = False
        self.calibration_coverage = 85.0 # Populated after held-out calibration
        self.average_interval_width = 18.0

    def fit(self, X: np.ndarray, y: np.ndarray):
        """Fits the 10th, 50th, and 90th percentile models on training feature data."""
        self.q10_model.fit(X, y)
        self.q50_model.fit(X, y)
        self.q90_model.fit(X, y)
        self.is_fitted = True

    def predict_interval(
        self,
        features: Dict[str, float],
        daily_consumption_lpd: float = 15.0
    ) -> Dict[str, Any]:
        """
        Produces prediction interval [Q_0.10, Q_0.90] and median estimate Q_0.50.
        Ensures monotonic ordering: Q_lower <= Q_median <= Q_upper.
        """
        if not self.is_fitted:
            raise RuntimeError("QuantileUncertaintyEngine must be fitted before predicting intervals.")

        X = features_dict_to_array(features)
        q10 = max(0.0, float(self.q10_model.predict(X)[0]))
        q50 = max(0.0, float(self.q50_model.predict(X)[0]))
        q90 = max(0.0, float(self.q90_model.predict(X)[0]))

        # Enforce consistency in case of quantile crossing
        q_lower = min(q10, q50, q90)
        q_upper = max(q10, q50, q90)
        q_median = np.clip(q50, q_lower, q_upper)

        daily_use = max(0.1, daily_consumption_lpd)
        width_days = q_upper - q_lower

        return {
            "model_version": self.model_version,
            "rul_median_days": round(float(q_median), 1),
            "rul_lower_days": round(float(q_lower), 1),
            "rul_upper_days": round(float(q_upper), 1),
            "rul_median_litres": round(float(q_median * daily_use), 1),
            "rul_lower_litres": round(float(q_lower * daily_use), 1),
            "rul_upper_litres": round(float(q_upper * daily_use), 1),
            "interval_width_days": round(float(width_days), 1),
            "nominal_coverage_pct": 80.0,
            "historical_empirical_coverage_pct": round(self.calibration_coverage, 1),
        }

    def evaluate_coverage(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Tuple[float, float]:
        """
        Computes empirical Prediction Interval Coverage Probability (PICP) and average width.
        """
        if not self.is_fitted or len(y_test) == 0:
            return 0.0, 0.0

        q10_preds = np.maximum(0.0, self.q10_model.predict(X_test))
        q90_preds = np.maximum(0.0, self.q90_model.predict(X_test))

        lower = np.minimum(q10_preds, q90_preds)
        upper = np.maximum(q10_preds, q90_preds)

        inside = (y_test >= lower) & (y_test <= upper)
        picp = float(np.mean(inside) * 100.0)
        mean_width = float(np.mean(upper - lower))

        self.calibration_coverage = picp
        self.average_interval_width = mean_width
        return picp, mean_width

    def save(self, filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as f:
            pickle.dump({
                "q10": self.q10_model,
                "q50": self.q50_model,
                "q90": self.q90_model,
                "coverage": self.calibration_coverage,
                "width": self.average_interval_width,
                "version": self.model_version,
            }, f)

    def load(self, filepath: str):
        with open(filepath, "rb") as f:
            data = pickle.load(f)
            self.q10_model = data["q10"]
            self.q50_model = data["q50"]
            self.q90_model = data["q90"]
            self.calibration_coverage = data.get("coverage", 85.0)
            self.average_interval_width = data.get("width", 18.0)
            self.model_version = data.get("version", self.model_version)
            self.is_fitted = True
