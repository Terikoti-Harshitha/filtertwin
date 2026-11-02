import pytest
import numpy as np
from app.evaluation.dataset_generator import generate_dataset_suite
from app.evaluation.data_split import split_scenarios_by_family
from app.evaluation.metrics import compute_regression_metrics, compute_interval_metrics, compute_anomaly_metrics
from app.intelligence.feature_engineering import extract_features_at_point, FEATURE_NAMES

def test_no_data_leakage_in_features():
    suite = generate_dataset_suite(num_scenarios=2, base_seed=123)
    obs = suite[0]["observations"]
    gt = suite[0]["ground_truth"]

    f = extract_features_at_point(obs)
    assert f is not None

    # Verify no ground truth columns exist in extracted features
    forbidden_keys = ["degradation_index", "true_rul_days", "true_rul_litres", "injected_fault_type", "is_eol"]
    for k in forbidden_keys:
        assert k not in f
        assert k not in FEATURE_NAMES

def test_disjoint_scenario_splits():
    suite = generate_dataset_suite(num_scenarios=20, base_seed=456)
    train, val, test = split_scenarios_by_family(suite, holdout_family="nonlinear")

    train_ids = {s["scenario_id"] for s in train}
    val_ids = {s["scenario_id"] for s in val}
    test_ids = {s["scenario_id"] for s in test}

    # Zero overlap
    assert len(train_ids.intersection(val_ids)) == 0
    assert len(train_ids.intersection(test_ids)) == 0
    assert len(val_ids.intersection(test_ids)) == 0

    # Ensure all 'nonlinear' scenarios are in test
    for s in test:
        if s["degradation_type"] == "nonlinear":
            assert s["scenario_id"] not in train_ids
            assert s["scenario_id"] not in val_ids

def test_metric_computations():
    y_true = np.array([100.0, 80.0, 60.0, 40.0])
    y_base = np.array([120.0, 100.0, 80.0, 60.0]) # MAE = 20.0
    y_pred = np.array([105.0, 85.0, 62.0, 42.0])  # MAE = 3.5

    reg = compute_regression_metrics(y_true, y_pred, baseline_mae=20.0)
    assert reg["mae"] == 3.5
    assert reg["improvement_pct"] == pytest.approx(82.5, 0.1)

    low = np.array([90.0, 75.0, 50.0, 30.0])
    high = np.array([110.0, 85.0, 70.0, 45.0])
    inter = compute_interval_metrics(y_true, low, high)
    assert inter["picp_coverage_pct"] == 100.0
    assert inter["average_interval_width"] == 16.25
