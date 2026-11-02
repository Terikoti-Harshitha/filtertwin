"""
Automated Model Training Pipeline.
Generates multi-scenario training datasets, extracts multivariable features,
trains Linear Regression, Gradient Boosting, and Quantile Uncertainty models,
and serializes artifacts into ml_artifacts/.
"""

import os
import sys
import numpy as np

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.evaluation.dataset_generator import generate_dataset_suite
from app.evaluation.data_split import split_scenarios_by_family
from app.intelligence.feature_engineering import extract_features_at_point, FEATURE_NAMES, features_dict_to_array
from app.intelligence.regression import LinearRegressionRULModel
from app.intelligence.gradient_boosting import GradientBoostingRULModel
from app.intelligence.uncertainty import QuantileUncertaintyEngine

def build_feature_matrix(scenarios):
    X_rows = []
    y_rows = []

    for sc in scenarios:
        obs = sc["observations"]
        gt = sc["ground_truth"]
        cap = sc["filter_capacity"]

        num_obs = len(obs)
        if num_obs < 5:
            continue

        # Extract features across multiple checkpoints in each scenario
        step_stride = max(1, num_obs // 8)
        for idx in range(3, num_obs, step_stride):
            f_dict = extract_features_at_point(
                obs,
                baseline_flow_lpm=2.0,
                nominal_capacity_l=cap,
                point_index=idx
            )
            if f_dict is not None:
                row = [f_dict[name] for name in FEATURE_NAMES]
                true_rul = float(gt[idx].true_rul_days)
                X_rows.append(row)
                y_rows.append(true_rul)

    return np.array(X_rows, dtype=np.float64), np.array(y_rows, dtype=np.float64)

def train_and_save_all(num_scenarios: int = 120):
    print(f"Generating {num_scenarios} training and validation scenarios...")
    suite = generate_dataset_suite(
        num_scenarios=num_scenarios,
        base_seed=42,
        degradation_types=["linear", "exponential"],
        include_faults=True,
    )

    train_scenarios, val_scenarios, _ = split_scenarios_by_family(suite, holdout_family="nonlinear")
    print(f"Dataset split: {len(train_scenarios)} training scenarios, {len(val_scenarios)} validation scenarios.")

    print("Extracting feature matrices...")
    X_train, y_train = build_feature_matrix(train_scenarios)
    X_val, y_val = build_feature_matrix(val_scenarios)
    print(f"Feature matrix dimensions: X_train: {X_train.shape}, X_val: {X_val.shape}")

    # 1. Train Linear Regression
    print("Training Multivariable Linear Regression...")
    lin_model = LinearRegressionRULModel()
    lin_model.fit(X_train, y_train)
    lin_path = os.path.join(settings.ML_ARTIFACTS_DIR, "linear_regression.pkl")
    lin_model.save(lin_path)
    print(f"Saved Linear Regression artifact to {lin_path}")

    # 2. Train Gradient Boosting
    print("Training Gradient Boosted Regressor...")
    gb_model = GradientBoostingRULModel()
    gb_model.fit(X_train, y_train)
    gb_path = os.path.join(settings.ML_ARTIFACTS_DIR, "gradient_boosting.pkl")
    gb_model.save(gb_path)
    print(f"Saved Gradient Boosting artifact to {gb_path}")

    # 3. Train Quantile Uncertainty Engine
    print("Training Quantile Uncertainty Engine (10th, 50th, 90th percentiles)...")
    unc_engine = QuantileUncertaintyEngine()
    unc_engine.fit(X_train, y_train)
    picp, width = unc_engine.evaluate_coverage(X_val, y_val)
    print(f"Calibration on validation set: PICP Coverage = {picp:.1f}%, Mean Width = {width:.1f} days")
    unc_path = os.path.join(settings.ML_ARTIFACTS_DIR, "uncertainty_engine.pkl")
    unc_engine.save(unc_path)
    print(f"Saved Quantile Uncertainty artifact to {unc_path}")

    print("All ML models trained and serialized successfully!")

if __name__ == "__main__":
    train_and_save_all()
