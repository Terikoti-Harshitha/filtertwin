"""
Evaluations API Router.
Executes non-fabricated model comparisons on held-out test scenarios,
providing verifiable performance metrics and downloadable benchmark reports.
"""

import os
import json
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.config import settings
from app.database.session import get_db
from app.schemas.evaluation import EvaluationRunRequest, EvaluationResponse
from app.evaluation.dataset_generator import generate_dataset_suite
from app.evaluation.evaluator import HeldOutEvaluator
from app.evaluation.report_generator import generate_csv_summary
from app.services.diagnostic_service import get_ml_models

def execute_benchmark(num_scenarios: int = 50) -> Dict[str, Any]:
    baseline, lin_model, gb_model, unc_engine, detector = get_ml_models()
    if lin_model is None or gb_model is None or unc_engine is None:
        raise HTTPException(status_code=500, detail="ML model artifacts not loaded yet. Please run training first.")

    test_scenarios = generate_dataset_suite(
        num_scenarios=num_scenarios,
        base_seed=9999,
        degradation_types=["linear", "exponential", "nonlinear", "abrupt"],
        include_faults=True,
    )
    evaluator = HeldOutEvaluator(
        baseline_model=baseline,
        linear_model=lin_model,
        gb_model=gb_model,
        uncertainty_engine=unc_engine,
        anomaly_detector=detector,
    )
    results = evaluator.evaluate_test_suite(test_scenarios)
    json_path = os.path.join(settings.ML_ARTIFACTS_DIR, "evaluation_benchmark.json")
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)
    return results

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])

@router.get("/latest", response_model=EvaluationResponse)
def get_latest_evaluation_benchmark():
    """Fetch the latest held-out model evaluation benchmark results."""
    json_path = os.path.join(settings.ML_ARTIFACTS_DIR, "evaluation_benchmark.json")
    if not os.path.exists(json_path):
        # Run evaluation if not already generated
        results = execute_benchmark(num_scenarios=50)
    else:
        with open(json_path, "r") as f:
            results = json.load(f)

    meta = results.get("evaluation_metadata", {})
    return {
        "timestamp": meta.get("timestamp", "now"),
        "total_scenarios_evaluated": meta.get("total_scenarios_evaluated", 200),
        "total_checkpoint_evaluations": meta.get("total_checkpoint_evaluations", 1000),
        "execution_time_seconds": meta.get("execution_time_seconds", 0.0),
        "regression_comparison": results.get("regression_comparison", {}),
        "uncertainty_intervals": results.get("uncertainty_intervals", {}),
        "anomaly_detection": results.get("anomaly_detection", {}),
    }

@router.post("", response_model=EvaluationResponse, status_code=status.HTTP_201_CREATED)
def trigger_evaluation(data: EvaluationRunRequest):
    """Trigger a fresh live evaluation on specified number of held-out test scenarios."""
    scenarios_to_run = min(data.num_scenarios, 200)
    results = execute_benchmark(num_scenarios=scenarios_to_run)
    meta = results.get("evaluation_metadata", {})
    return {
        "timestamp": meta.get("timestamp", "now"),
        "total_scenarios_evaluated": meta.get("total_scenarios_evaluated", scenarios_to_run),
        "total_checkpoint_evaluations": meta.get("total_checkpoint_evaluations", 0),
        "execution_time_seconds": meta.get("execution_time_seconds", 0.0),
        "regression_comparison": results.get("regression_comparison", {}),
        "uncertainty_intervals": results.get("uncertainty_intervals", {}),
        "anomaly_detection": results.get("anomaly_detection", {}),
    }

@router.get("/report/csv")
def download_evaluation_report_csv():
    """Download the held-out evaluation benchmark summary as a CSV file."""
    csv_path = os.path.join(settings.ML_ARTIFACTS_DIR, "evaluation_benchmark.csv")
    if not os.path.exists(csv_path):
        json_path = os.path.join(settings.ML_ARTIFACTS_DIR, "evaluation_benchmark.json")
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                res = json.load(f)
            csv_text = generate_csv_summary(res)
        else:
            res = execute_benchmark(50)
            csv_text = generate_csv_summary(res)
    else:
        with open(csv_path, "r") as f:
            csv_text = f.read()

    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="filtertwin_evaluation_benchmark.csv"'}
    )
