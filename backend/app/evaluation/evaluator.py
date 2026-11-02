"""
Comprehensive Model and Diagnostic Evaluator.
Executes batch evaluation on held-out test scenarios, extracting multi-point observations,
querying models, and computing real (non-fabricated) benchmark metrics.
"""

import time
import numpy as np
from typing import List, Dict, Any, Optional

from app.intelligence.feature_engineering import extract_features_at_point, FEATURE_NAMES, features_dict_to_array
from app.intelligence.baseline import FixedVolumeBaseline
from app.intelligence.regression import LinearRegressionRULModel
from app.intelligence.gradient_boosting import GradientBoostingRULModel
from app.intelligence.uncertainty import QuantileUncertaintyEngine
from app.intelligence.anomaly_detection import AnomalyDetector
from app.evaluation.metrics import compute_regression_metrics, compute_interval_metrics, compute_anomaly_metrics

class HeldOutEvaluator:
    def __init__(
        self,
        baseline_model: FixedVolumeBaseline,
        linear_model: LinearRegressionRULModel,
        gb_model: GradientBoostingRULModel,
        uncertainty_engine: QuantileUncertaintyEngine,
        anomaly_detector: AnomalyDetector,
    ):
        self.baseline = baseline_model
        self.linear_model = linear_model
        self.gb_model = gb_model
        self.uncertainty = uncertainty_engine
        self.anomaly_detector = anomaly_detector

    def evaluate_test_suite(
        self,
        test_scenarios: List[Dict[str, Any]],
        sample_points_per_scenario: int = 5
    ) -> Dict[str, Any]:
        """
        Evaluates models across multiple observation checkpoints for every test scenario.
        """
        start_time = time.time()

        y_true_rul = []
        y_pred_baseline = []
        y_pred_linear = []
        y_pred_gb = []

        q_lower = []
        q_upper = []

        true_categories = []
        pred_categories = []
        fault_types_recorded = []

        for sc in test_scenarios:
            obs = sc["observations"]
            gt = sc["ground_truth"]
            cap = sc["filter_capacity"]
            daily_use = sc["daily_consumption"]
            f_type = sc["injected_fault_type"]

            num_obs = len(obs)
            if num_obs < 10:
                continue

            # Pick multiple time horizons (e.g. 20%, 40%, 60%, 80%, 95% through scenario)
            checkpoints = [
                int(num_obs * frac) for frac in [0.25, 0.45, 0.65, 0.85, 0.95]
                if int(num_obs * frac) < num_obs
            ]

            for cp in checkpoints:
                # Sub-history up to checkpoint
                sub_obs = obs[:cp + 1]
                gt_point = gt[cp]

                features = extract_features_at_point(
                    sub_obs,
                    baseline_flow_lpm=2.0,
                    nominal_capacity_l=cap,
                    point_index=cp
                )

                if features is None:
                    continue

                actual_rul_days = float(gt_point.true_rul_days)
                cum_vol = float(features["cumulative_volume_l"])

                # 1. Baseline
                base_res = self.baseline.predict(
                    cumulative_volume_l=cum_vol,
                    filter_capacity_l=cap,
                    daily_consumption_lpd=daily_use
                )
                pred_base = base_res["rul_days"]

                # 2. Linear Regression
                pred_lin = self.linear_model.predict(features, daily_consumption_lpd=daily_use)["rul_days"]

                # 3. Gradient Boosting
                pred_gbr = self.gb_model.predict(features, daily_consumption_lpd=daily_use)["rul_days"]

                # 4. Uncertainty Interval
                interval = self.uncertainty.predict_interval(features, daily_consumption_lpd=daily_use)
                q_low = interval["rul_lower_days"]
                q_up = interval["rul_upper_days"]

                # 5. Anomaly Detection
                diag = self.anomaly_detector.evaluate(
                    sub_obs,
                    filter_capacity_l=cap,
                    baseline_flow_lpm=2.0
                )
                pred_cat = diag["category"]

                # Ground truth diagnostic condition
                deg_idx = gt_point.degradation_index
                active_f = gt_point.injected_fault_type

                if active_f in ["flow_drop", "tds_spike"]:
                    true_cat = "ABRUPT_ANOMALY"
                elif active_f == "sensor_disconnection":
                    true_cat = "INSUFFICIENT_DATA"
                elif deg_idx >= 0.70 or active_f in ["sensor_drift", "gradual_wear"]:
                    true_cat = "GRADUAL_WEAR"
                else:
                    true_cat = "NORMAL"

                # Append records
                y_true_rul.append(actual_rul_days)
                y_pred_baseline.append(pred_base)
                y_pred_linear.append(pred_lin)
                y_pred_gb.append(pred_gbr)

                q_lower.append(q_low)
                q_upper.append(q_up)

                true_categories.append(true_cat)
                pred_categories.append(pred_cat)
                fault_types_recorded.append(active_f)

        y_true_arr = np.array(y_true_rul)
        y_base_arr = np.array(y_pred_baseline)
        y_lin_arr = np.array(y_pred_linear)
        y_gb_arr = np.array(y_pred_gb)

        # Baseline error
        baseline_metrics = compute_regression_metrics(y_true_arr, y_base_arr)
        linear_metrics = compute_regression_metrics(y_true_arr, y_lin_arr, baseline_mae=baseline_metrics["mae"])
        gb_metrics = compute_regression_metrics(y_true_arr, y_gb_arr, baseline_mae=baseline_metrics["mae"])

        # Uncertainty metrics
        interval_metrics = compute_interval_metrics(y_true_arr, np.array(q_lower), np.array(q_upper))

        # Anomaly classification metrics
        anomaly_metrics = compute_anomaly_metrics(true_categories, pred_categories, fault_types_recorded)

        elapsed = time.time() - start_time

        return {
            "evaluation_metadata": {
                "total_scenarios_evaluated": len(test_scenarios),
                "total_checkpoint_evaluations": len(y_true_rul),
                "execution_time_seconds": round(elapsed, 2),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            "regression_comparison": {
                "fixed_volume_baseline": baseline_metrics,
                "linear_regression": linear_metrics,
                "gradient_boosting": gb_metrics,
            },
            "uncertainty_intervals": interval_metrics,
            "anomaly_detection": anomaly_metrics,
        }
