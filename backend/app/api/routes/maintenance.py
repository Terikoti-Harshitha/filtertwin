"""
Maintenance API Router.
Handles guided maintenance procedures, checklists, completion records,
and re-baselining virtual purifier operating parameters.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.schemas.maintenance import GuideResponse, MaintenanceRecordCreate, MaintenanceRecordResponse
from app.maintenance.guide_service import get_all_guides, get_guide_by_id
from app.models.entities import MaintenanceRecord, PurifierProfile

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])

@router.get("/guides", response_model=List[GuideResponse])
def list_guides():
    """Retrieve all available standard manufacturer replacement guides."""
    return get_all_guides()

@router.get("/guides/{guide_id}", response_model=GuideResponse)
def get_guide(guide_id: str):
    """Retrieve details and step-by-step checklist for a specific filter replacement."""
    guide = get_guide_by_id(guide_id)
    if not guide:
        raise HTTPException(status_code=404, detail="Maintenance guide not found")
    return guide

@router.post("/records", response_model=MaintenanceRecordResponse, status_code=status.HTTP_201_CREATED)
def record_maintenance(data: MaintenanceRecordCreate, db: Session = Depends(get_db)):
    """
    Log completion of a filter replacement checklist and re-establish
    clean baseline monitoring metrics for the purifier.
    """
    purifier = db.query(PurifierProfile).filter(PurifierProfile.id == data.purifier_profile_id).first()
    if not purifier:
        raise HTTPException(status_code=404, detail="Purifier profile not found")

    record = MaintenanceRecord(
        purifier_profile_id=data.purifier_profile_id,
        guide_id=data.guide_id,
        replacement_type=data.replacement_type,
        technician_notes=data.technician_notes,
        checklist_completed_json=data.checklist_completed,
        reset_baseline_flow=data.reset_baseline_flow,
        reset_baseline_rejection=data.reset_baseline_rejection,
    )
    db.add(record)

    # Re-establish purifier baseline flow rate
    purifier.initial_flow_rate_lpm = data.reset_baseline_flow
    db.commit()
    db.refresh(record)

    return record

@router.get("/records", response_model=List[MaintenanceRecordResponse])
def get_maintenance_history(purifier_id: str = None, db: Session = Depends(get_db)):
    """Fetch past maintenance and filter replacement history."""
    q = db.query(MaintenanceRecord)
    if purifier_id:
        q = q.filter(MaintenanceRecord.purifier_profile_id == purifier_id)
    return q.order_by(MaintenanceRecord.completed_at.desc()).all()
