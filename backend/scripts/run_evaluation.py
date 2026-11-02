"""
Held-out Evaluation Benchmark Script.
Evaluates pre-trained models on 200+ held-out scenarios (including unseen nonlinear degradation),
computes non-fabricated benchmark metrics, and saves the verified report.
"""

import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.evaluation.dataset_generator import generate_dataset_suite
from app.evaluation.evaluator import HeldOutEvaluator
from app.evaluation.report_generator import generate_csv_summary
from app.intelligence.baseline import FixedVolumeBaseline
from app.intelligence.regression import LinearRegressionRULModel
from app.intelligence.gradient_boosting import GradientBoostingRULModel
from app.intelligence.uncertainty import QuantileUncertaintyEngine
from app.intelligence.anomaly_detection import AnomalyDetector

def run_heldout_evaluation(num_test_scenarios: int = 200):
    print(f"Loading trained models from {settings.ML_ARTIFACTS_DIR}...")
    baseline = FixedVolumeBaseline()

    lin_model = LinearRegressionRULModel()
    lin_model.load(os.path.join(settings.ML_ARTIFACTS_DIR, "linear_regression.pkl"))

    gb_model = GradientBoostingRULModel()
    gb_model.load(os.path.join(settings.ML_ARTIFACTS_DIR, "gradient_boosting.pkl"))

    unc_engine = QuantileUncertaintyEngine()
    unc_engine.load(os.path.join(settings.ML_ARTIFACTS_DIR, "uncertainty_engine.pkl"))

    detector = AnomalyDetector()

    print(f"Generating {num_test_scenarios} held-out test scenarios (including unseen nonlinear degradation & faults)...")
    test_scenarios = generate_dataset_suite(
        num_scenarios=num_test_scenarios,
        base_seed=9999,
        degradation_types=["linear", "exponential", "nonlinear", "abrupt"],
        include_faults=True,
    )

    print("Running evaluation across multi-point observation checkpoints...")
    evaluator = HeldOutEvaluator(
        baseline_model=baseline,
        linear_model=lin_model,
        gb_model=gb_model,
        uncertainty_engine=unc_engine,
        anomaly_detector=detector,
    )

    results = evaluator.evaluate_test_suite(test_scenarios)

    # Save JSON report
    json_path = os.path.join(settings.ML_ARTIFACTS_DIR, "evaluation_benchmark.json")
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)

    # Save CSV summary
    csv_content = generate_csv_summary(results)
    csv_path = os.path.join(settings.ML_ARTIFACTS_DIR, "evaluation_benchmark.csv")
    with open(csv_path, "w") as f:
        f.write(csv_content)

    print(f"\n================ BENCHMARK RESULTS ================")
    reg = results["regression_comparison"]
    print(f"Fixed-Volume Baseline   : MAE = {reg['fixed_volume_baseline']['mae']} days | RMSE = {reg['fixed_volume_baseline']['rmse']} days")
    print(f"Linear Regression       : MAE = {reg['linear_regression']['mae']} days | RMSE = {reg['linear_regression']['rmse']} days | Improvement: {reg['linear_regression']['improvement_pct']}%")
    print(f"Gradient Boosted Trees  : MAE = {reg['gradient_boosting']['mae']} days | RMSE = {reg['gradient_boosting']['rmse']} days | Improvement: {reg['gradient_boosting']['improvement_pct']}%")

    unc = results["uncertainty_intervals"]
    print(f"\nPrediction Intervals    : PICP Coverage = {unc['picp_coverage_pct']}% | Average Width = {unc['average_interval_width']} days")

    anom = results["anomaly_detection"]
    print(f"\nAnomaly Detection       : Precision = {anom['precision']} | Recall = {anom['recall']} | F1 = {anom['f1_score']} | False Alert Rate = {anom['false_alert_rate_pct']}%")
    print(f"Per-fault Detection %   : {anom['per_fault_detection_pct']}")
    print(f"Saved benchmark report to:\n  - {json_path}\n  - {csv_path}\n===================================================\n")

    return results

if __name__ == "__main__":
    run_heldout_evaluation()
