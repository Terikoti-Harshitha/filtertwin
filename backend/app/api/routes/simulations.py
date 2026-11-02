"""
Simulations API Router.
Controls scenario initialization, time progression, telemetry reading queries,
fault injection, and restricted evaluation ground-truth access.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.session import get_db
from app.schemas.simulation import (
    SimulationCreate, FaultInjectRequest, SimulationResponse, ReadingResponse, GroundTruthResponse
)
from app.services.purifier_service import get_purifier_by_id
from app.services.simulation_service import (
    create_and_run_simulation, get_simulation_by_id, get_simulations_for_purifier,
    get_readings_for_simulation, get_ground_truth_for_simulation, inject_fault_into_simulation
)

router = APIRouter(prefix="/simulations", tags=["Simulations"])

@router.post("", response_model=SimulationResponse, status_code=status.HTTP_201_CREATED)
def start_simulation(data: SimulationCreate, db: Session = Depends(get_db)):
    """Initialize and run a new purifier simulation run."""
    purifier = get_purifier_by_id(db, data.purifier_profile_id)
    if not purifier:
        raise HTTPException(status_code=404, detail="Referenced purifier profile does not exist")

    run, readings = create_and_run_simulation(db, purifier, data)
    resp = SimulationResponse.model_validate(run)
    if readings:
        resp.latest_reading = ReadingResponse.model_validate(readings[-1])
    return resp

@router.get("/{sim_id}", response_model=SimulationResponse)
def get_simulation_status(sim_id: str, db: Session = Depends(get_db)):
    """Retrieve execution status and metadata for a simulation run."""
    run = get_simulation_by_id(db, sim_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation run not found")
    readings = get_readings_for_simulation(db, sim_id)
    resp = SimulationResponse.model_validate(run)
    if readings:
        resp.latest_reading = ReadingResponse.model_validate(readings[-1])
    return resp

@router.get("/{sim_id}/readings", response_model=List[ReadingResponse])
def get_readings(
    sim_id: str,
    limit: Optional[int] = Query(None, description="Max readings to return"),
    db: Session = Depends(get_db)
):
    """Retrieve observed time-series sensor readings for charts and monitoring."""
    readings = get_readings_for_simulation(db, sim_id, limit=limit)
    return [ReadingResponse.model_validate(r) for r in readings]

@router.get("/{sim_id}/ground-truth", response_model=List[GroundTruthResponse])
def get_ground_truth(
    sim_id: str,
    db: Session = Depends(get_db)
):
    """
    EVALUATION-ONLY ENDPOINT.
    Returns hidden degradation states. Strictly forbidden from normal prediction telemetry feeds.
    """
    gt_list = get_ground_truth_for_simulation(db, sim_id)
    return [GroundTruthResponse.model_validate(gt) for gt in gt_list]

@router.post("/{sim_id}/inject-fault", status_code=status.HTTP_200_OK)
def inject_fault(sim_id: str, data: FaultInjectRequest, db: Session = Depends(get_db)):
    """Dynamically introduce a physical or sensor fault into an active simulation."""
    success = inject_fault_into_simulation(db, sim_id, data)
    if not success:
        raise HTTPException(status_code=404, detail="Simulation run not found")
    return {"message": f"Successfully injected {data.fault_type} fault at day {data.start_day}"}

@router.post("/{sim_id}/pause", status_code=status.HTTP_200_OK)
def pause_simulation(sim_id: str, db: Session = Depends(get_db)):
    run = get_simulation_by_id(db, sim_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation run not found")
    run.status = "paused"
    db.commit()
    return {"status": "paused"}

@router.post("/{sim_id}/resume", status_code=status.HTTP_200_OK)
def resume_simulation(sim_id: str, db: Session = Depends(get_db)):
    run = get_simulation_by_id(db, sim_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation run not found")
    run.status = "running"
    db.commit()
    return {"status": "running"}

@router.post("/{sim_id}/reset", status_code=status.HTTP_200_OK)
def reset_simulation(sim_id: str, db: Session = Depends(get_db)):
    run = get_simulation_by_id(db, sim_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation run not found")
    run.status = "idle"
    run.current_day = 0.0
    run.cumulative_volume_l = 0.0
    db.commit()
    return {"status": "idle", "message": "Simulation reset to day 0"}
