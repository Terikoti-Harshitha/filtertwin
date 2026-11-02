"""
Diagnostics and Predictive Intelligence API Router.
Generates multivariable RUL predictions, prediction uncertainty intervals,
anomaly classifications, alerts, and explainability factors.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database.session import get_db
from app.schemas.diagnostic import FullDiagnosticResponse, AlertResponse
from app.services.diagnostic_service import (
    run_diagnostic_for_simulation, get_alerts_for_simulation
)
from app.models.entities import Prediction

router = APIRouter(prefix="/diagnostics", tags=["Diagnostics"])

@router.post("/{simulation_id}/predict", response_model=FullDiagnosticResponse)
def generate_prediction(simulation_id: str, db: Session = Depends(get_db)):
    """
    Trigger real-time diagnostic evaluation on current observations of a simulation.
    Generates Baseline, Linear Regression, Gradient Boosting RUL, Quantile Interval, and Explainability.
    """
    try:
        diag = run_diagnostic_for_simulation(db, simulation_id)
        return diag
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnostic error: {str(e)}")

@router.get("/{simulation_id}/latest", response_model=FullDiagnosticResponse)
def get_latest_diagnosis(simulation_id: str, db: Session = Depends(get_db)):
    """Fetch the latest diagnosis for a simulation."""
    return generate_prediction(simulation_id, db)

@router.get("/{simulation_id}/alerts", response_model=List[AlertResponse])
def get_alerts(simulation_id: str, db: Session = Depends(get_db)):
    """Fetch all diagnostic alerts recorded for this simulation."""
    alerts = get_alerts_for_simulation(db, simulation_id)
    return [AlertResponse.model_validate(a) for a in alerts]
