"""
Pydantic Schemas for Predictions, Diagnostics, Alerts, and Explainability.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ContributingFactor(BaseModel):
    factor: str
    observed_value: str
    direction: str
    impact_magnitude: float
    description: str

class ExplanationResponse(BaseModel):
    diagnostic_category: str
    diagnostic_subtype: str
    contributing_factors: List[ContributingFactor]
    observed_evidence: List[str]
    recommended_action: str
    action_summary: str
    disclaimer: str

class PredictionDetail(BaseModel):
    model_version: str
    method: str
    rul_days: float
    rul_litres: float
    is_adaptive: bool

class IntervalDetail(BaseModel):
    model_version: str
    rul_median_days: float
    rul_lower_days: float
    rul_upper_days: float
    rul_median_litres: float
    rul_lower_litres: float
    rul_upper_litres: float
    interval_width_days: float
    nominal_coverage_pct: float
    historical_empirical_coverage_pct: float

class DiagnosisDetail(BaseModel):
    category: str
    subtype: str
    confidence: float
    severity: str
    message: str
    evidence: List[str]
    suppress_rul: bool

class FullDiagnosticResponse(BaseModel):
    simulation_id: str
    simulated_day: float
    data_quality_status: str
    data_quality_message: str
    baseline_prediction: PredictionDetail
    linear_prediction: PredictionDetail
    gradient_boosting_prediction: PredictionDetail
    uncertainty_interval: IntervalDetail
    diagnosis: DiagnosisDetail
    explanation: ExplanationResponse

class AlertResponse(BaseModel):
    id: str
    simulation_run_id: str
    timestamp: str
    simulated_day: float
    category: str
    subtype: str
    severity: str
    message: str
    evidence_json: Optional[List[str]] = None
    is_acknowledged: bool
    created_at: datetime

    class Config:
        from_attributes = True
