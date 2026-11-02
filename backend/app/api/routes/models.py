"""
Models API Router.
Exposes metadata about available predictive ML and baseline algorithms.
"""

from fastapi import APIRouter
from typing import List, Dict, Any

router = APIRouter(prefix="/models", tags=["Models"])

AVAILABLE_MODELS = [
    {
        "id": "fixed-volume-baseline-v1",
        "name": "Fixed-Volume Baseline",
        "type": "Heuristic Benchmark",
        "description": "Calculates RUL using simple static rated capacity subtraction (Capacity - Cumulative Volume) / Daily Usage.",
        "is_adaptive": False,
        "features": ["cumulative_volume_l", "daily_consumption_lpd"],
    },
    {
        "id": "linear-regression-v1",
        "name": "Multivariable Linear Regression",
        "type": "Linear Statistical Model",
        "description": "Ridge regularized regression fitted on standardized multi-signal telemetry features with linear coefficient contributions.",
        "is_adaptive": True,
        "features": ["cumulative_volume_l", "tds_load_g", "flow_ratio", "rejection_percentage", "rejection_trend", "daily_consumption_lpd", "filter_age_days", "rolling_flow_lpm"],
    },
    {
        "id": "gradient-boosting-v1",
        "name": "Gradient Boosted Trees (HistGradientBoosting)",
        "type": "Ensemble Nonlinear Model",
        "description": "Gradient boosted decision trees capable of modeling complex nonlinear interactions between cumulative volume, flow degradation, and TDS exposure.",
        "is_adaptive": True,
        "features": ["cumulative_volume_l", "tds_load_g", "flow_ratio", "rejection_percentage", "rejection_trend", "daily_consumption_lpd", "filter_age_days", "rolling_flow_lpm"],
    },
    {
        "id": "quantile-regressor-v1",
        "name": "Quantile Uncertainty Engine",
        "type": "Quantile Gradient Boosting",
        "description": "Trained across 10th, 50th, and 90th percentiles to generate calibrated 80% prediction intervals [Q_0.10, Q_0.90].",
        "is_adaptive": True,
        "features": ["cumulative_volume_l", "tds_load_g", "flow_ratio", "rejection_percentage", "rejection_trend", "daily_consumption_lpd", "filter_age_days", "rolling_flow_lpm"],
    },
]

@router.get("", response_model=List[Dict[str, Any]])
def list_models():
    """List available predictive maintenance models and heuristics."""
    return AVAILABLE_MODELS

@router.get("/{model_id}")
def get_model(model_id: str):
    """Get metadata for a specific model."""
    for m in AVAILABLE_MODELS:
        if m["id"] == model_id:
            return m
    return AVAILABLE_MODELS[0]
