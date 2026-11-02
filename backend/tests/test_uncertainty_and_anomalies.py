import pytest
import numpy as np
from app.intelligence.uncertainty import QuantileUncertaintyEngine
from app.intelligence.anomaly_detection import AnomalyDetector, DiagnosticCategory, AnomalySubtype
from app.intelligence.explainability import generate_diagnostic_explanation
from app.intelligence.feature_engineering import FEATURE_NAMES

def test_quantile_uncertainty_bounds():
    # Synthetic dataset
    np.random.seed(42)
    X = np.random.rand(60, len(FEATURE_NAMES)) * 100
    y = np.maximum(0.0, 300.0 - (X[:, 0] * 1.5) + np.random.randn(60) * 10.0)

    engine = QuantileUncertaintyEngine()
    engine.fit(X, y)

    sample_f = {name: float(X[0, i]) for i, name in enumerate(FEATURE_NAMES)}
    interval = engine.predict_interval(sample_f, daily_consumption_lpd=15.0)

    assert interval["rul_lower_days"] <= interval["rul_median_days"] <= interval["rul_upper_days"]
    assert interval["interval_width_days"] >= 0

    picp, width = engine.evaluate_coverage(X, y)
    assert 0.0 <= picp <= 100.0
    assert width > 0

def test_anomaly_detection_normal_state():
    detector = AnomalyDetector()
    readings = [
        {
            "flow_rate_lpm": 1.95,
            "inlet_tds_ppm": 500.0,
            "outlet_tds_ppm": 25.0,
            "rejection_percentage": 95.0,
            "cumulative_volume_l": 500.0,
            "simulated_day": float(i),
            "sensor_status": "normal",
        }
        for i in range(10)
    ]
    diag = detector.evaluate(readings)
    assert diag["category"] == DiagnosticCategory.NORMAL.value
    assert diag["suppress_rul"] is False

def test_anomaly_detection_flow_drop():
    detector = AnomalyDetector()
    readings = [
        {
            "flow_rate_lpm": 2.0,
            "inlet_tds_ppm": 500.0,
            "outlet_tds_ppm": 25.0,
            "rejection_percentage": 95.0,
            "cumulative_volume_l": 500.0,
            "simulated_day": float(i),
            "sensor_status": "normal",
        }
        for i in range(10)
    ]
    # Inject sudden acute flow drop
    readings.append({
        "flow_rate_lpm": 0.60,
        "inlet_tds_ppm": 500.0,
        "outlet_tds_ppm": 25.0,
        "rejection_percentage": 95.0,
        "cumulative_volume_l": 510.0,
        "simulated_day": 10.0,
        "sensor_status": "abrupt_anomaly",
    })
    diag = detector.evaluate(readings)
    assert diag["category"] == DiagnosticCategory.ABRUPT_ANOMALY.value
    assert diag["subtype"] == AnomalySubtype.FLOW_DROP.value

def test_anomaly_detection_insufficient_data():
    detector = AnomalyDetector()
    # Missing sensor data
    readings = [
        {"flow_rate_lpm": -1.0, "inlet_tds_ppm": 500.0, "outlet_tds_ppm": -1.0, "sensor_status": "insufficient_data"}
    ]
    diag = detector.evaluate(readings)
    assert diag["category"] == DiagnosticCategory.INSUFFICIENT_DATA.value
    assert diag["suppress_rul"] is True

def test_explainability_generation():
    features = {
        "flow_ratio": 0.65,
        "tds_load_g": 2500.0,
        "rejection_percentage": 82.0,
        "rejection_trend": -14.0,
        "cumulative_volume_l": 4500.0,
    }
    diagnosis = {
        "category": "GRADUAL_WEAR",
        "subtype": "progressive_clogging",
        "evidence": ["Flow ratio has declined to 65% of baseline."],
    }
    contribs = {"flow_ratio": -15.0, "tds_load_g": -8.0, "rejection_trend": -12.0}

    explanation = generate_diagnostic_explanation(features, contribs, diagnosis)
    assert explanation["diagnostic_category"] == "GRADUAL_WEAR"
    assert len(explanation["contributing_factors"]) >= 3
    assert explanation["recommended_action"] != ""
    assert "disclaimer" in explanation
