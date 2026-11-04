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
    SimulationCreate, FaultInjectRequest, SimulationResponse, ReadingResponse, GroundTruthResponse, TelemetryIngestRequest
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

@router.get("/telemetry/ingest", tags=["Simulations"])
def telemetry_ingest_info():
    """Information endpoint confirming telemetry receiver status for browser visitors."""
    return {
        "status": "online",
        "service": "FilterTwin IoT Ingestion Receiver",
        "description": "Ready to accept live sensor telemetry from physical ESP32 or Wokwi virtual hardware.",
        "method_required": "POST",
        "sample_payload": {
            "device_id": "wokwi-esp32-01",
            "flow_rate_lpm": 2.1,
            "inlet_tds_ppm": 550.0,
            "outlet_tds_ppm": 38.0,
            "rejection_percentage": 93.1,
            "sensor_status": "normal"
        }
    }

@router.post("/telemetry/ingest", status_code=status.HTTP_201_CREATED)
def ingest_telemetry(data: TelemetryIngestRequest, db: Session = Depends(get_db)):
    """
    Ingest live telemetry from physical ESP32 or Wokwi virtual micro-controller.
    Updates active digital twin and stores sensor reading.
    """
    from datetime import datetime
    from app.models.entities import SensorReading, PurifierProfile, SimulationRun

    run = db.query(SimulationRun).order_by(SimulationRun.created_at.desc()).first()
    if not run:
        purifier = db.query(PurifierProfile).first()
        if not purifier:
            raise HTTPException(status_code=400, detail="No purifier profile configured.")
        run, _ = create_and_run_simulation(
            db, purifier, SimulationCreate(purifier_profile_id=purifier.id, duration_days=30)
        )

    next_day = round(run.current_day + 0.1, 2)
    vol = data.cumulative_volume_l if data.cumulative_volume_l is not None else round(run.cumulative_volume_l + (data.flow_rate_lpm * 0.05), 2)
    rej = data.rejection_percentage if data.rejection_percentage is not None else (
        round(((data.inlet_tds_ppm - data.outlet_tds_ppm) / data.inlet_tds_ppm) * 100.0, 2) if data.inlet_tds_ppm > 0 else 0.0
    )

    reading = SensorReading(
        simulation_run_id=run.id,
        timestamp=datetime.utcnow().isoformat(),
        simulated_day=next_day,
        cumulative_volume_l=vol,
        flow_rate_lpm=data.flow_rate_lpm,
        inlet_tds_ppm=data.inlet_tds_ppm,
        outlet_tds_ppm=data.outlet_tds_ppm,
        rejection_percentage=rej,
        sensor_status=data.sensor_status or "normal"
    )
    db.add(reading)
    run.current_day = next_day
    run.cumulative_volume_l = vol
    db.commit()
    db.refresh(reading)

    return {
        "status": "ingested",
        "device_id": data.device_id,
        "reading_id": reading.id,
        "simulation_id": run.id,
        "simulated_day": next_day,
        "flow_rate_lpm": data.flow_rate_lpm,
        "outlet_tds_ppm": data.outlet_tds_ppm,
        "rejection_percentage": rej,
    }
