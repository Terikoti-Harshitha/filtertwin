"""
Pydantic Schemas for Evaluation Framework.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class EvaluationRunRequest(BaseModel):
    num_scenarios: int = Field(default=200, ge=10, le=500)
    include_faults: bool = True

class ModelMetricItem(BaseModel):
    mae: float
    rmse: float
    improvement_pct: float

class UncertaintyMetricItem(BaseModel):
    picp_coverage_pct: float
    average_interval_width: float

class AnomalyMetricItem(BaseModel):
    precision: float
    recall: float
    f1_score: float
    false_alert_rate_pct: float
    total_evaluated_instances: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    per_fault_detection_pct: Dict[str, float]
    confusion_matrix: Dict[str, Any]

class EvaluationResponse(BaseModel):
    id: Optional[str] = None
    timestamp: str
    total_scenarios_evaluated: int
    total_checkpoint_evaluations: int
    execution_time_seconds: float
    regression_comparison: Dict[str, ModelMetricItem]
    uncertainty_intervals: UncertaintyMetricItem
    anomaly_detection: AnomalyMetricItem
