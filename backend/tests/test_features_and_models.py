import pytest
import numpy as np
from app.simulator.engine import PurifierSimulator
from app.intelligence.feature_engineering import extract_features_at_point, FEATURE_NAMES, features_dict_to_array
from app.intelligence.baseline import FixedVolumeBaseline
from app.intelligence.regression import LinearRegressionRULModel
from app.intelligence.gradient_boosting import GradientBoostingRULModel

def test_feature_extraction():
    sim = PurifierSimulator(random_seed=42)
    obs, _ = sim.run_simulation(duration_days=30.0)
    features = extract_features_at_point(obs, baseline_flow_lpm=2.0, nominal_capacity_l=5000.0)

    assert features is not None
    for name in FEATURE_NAMES:
        assert name in features
    assert features["flow_ratio"] > 0.0
    assert features["filter_age_days"] == 29.0
    arr = features_dict_to_array(features)
    assert arr.shape == (1, len(FEATURE_NAMES))

def test_fixed_volume_baseline():
    baseline = FixedVolumeBaseline()
    pred = baseline.predict(cumulative_volume_l=3000.0, filter_capacity_l=5000.0, daily_consumption_lpd=20.0)
    assert pred["rul_litres"] == 2000.0
    assert pred["rul_days"] == 100.0
    assert pred["is_adaptive"] is False

def test_linear_regression_model():
    # Synthetic dataset
    X = np.array([
        [100, 50, 0.95, 95, 0, 15, 10, 1.9],
        [1500, 750, 0.85, 90, -5, 15, 100, 1.7],
        [3000, 1500, 0.70, 80, -15, 15, 200, 1.4],
        [4800, 2400, 0.50, 70, -25, 15, 320, 1.0],
    ])
    y = np.array([350.0, 265.0, 165.0, 45.0])

    model = LinearRegressionRULModel()
    model.fit(X, y)

    features = {
        "cumulative_volume_l": 2000.0,
        "tds_load_g": 1000.0,
        "flow_ratio": 0.80,
        "rejection_percentage": 88.0,
        "rejection_trend": -7.0,
        "daily_consumption_lpd": 15.0,
        "filter_age_days": 133.0,
        "rolling_flow_lpm": 1.6,
    }

    pred = model.predict(features)
    assert pred["rul_days"] > 0
    assert "feature_contributions" in pred
    assert len(pred["feature_contributions"]) == len(FEATURE_NAMES)

def test_gradient_boosting_model():
    X = np.random.rand(50, len(FEATURE_NAMES)) * 100
    y = 300.0 - (X[:, 0] * 2.0) + np.random.randn(50) * 5.0
    y = np.maximum(0.0, y)

    model = GradientBoostingRULModel()
    model.fit(X, y)

    features = {name: float(X[0, i]) for i, name in enumerate(FEATURE_NAMES)}
    pred = model.predict(features)
    assert pred["rul_days"] >= 0
    assert "Gradient Boosted Trees" in pred["method"]
