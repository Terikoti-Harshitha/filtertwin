"""
Purifier Profile Service.
Handles CRUD and configuration persistence for virtual water purifiers.
"""

from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.entities import PurifierProfile, FilterProfile
from app.schemas.purifier import PurifierCreate, PurifierUpdate

def get_purifiers(db: Session, skip: int = 0, limit: int = 100) -> List[PurifierProfile]:
    return db.query(PurifierProfile).offset(skip).limit(limit).all()

def get_purifier_by_id(db: Session, purifier_id: str) -> Optional[PurifierProfile]:
    return db.query(PurifierProfile).filter(PurifierProfile.id == purifier_id).first()

def create_purifier(db: Session, data: PurifierCreate) -> PurifierProfile:
    profile = PurifierProfile(
        name=data.name,
        location=data.location,
        initial_inlet_tds=data.initial_inlet_tds,
        daily_consumption_l=data.daily_consumption_l,
        initial_flow_rate_lpm=data.initial_flow_rate_lpm,
        filter_capacity_l=data.filter_capacity_l,
        nominal_lifetime_days=data.nominal_lifetime_days,
        degradation_type=data.degradation_type,
        degradation_speed=data.degradation_speed,
        sensor_noise=data.sensor_noise,
        sensor_drift=data.sensor_drift,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    # Attach default 3-stage filter profiles
    stages = [
        FilterProfile(purifier_profile_id=profile.id, stage_number=1, stage_name="Sediment Pre-Filter", cartridge_type="5-Micron Spun Polypropylene", rated_capacity_l=profile.filter_capacity_l * 0.4, expected_life_days=180),
        FilterProfile(purifier_profile_id=profile.id, stage_number=2, stage_name="Activated Carbon Block", cartridge_type="Extruded Carbon Block", rated_capacity_l=profile.filter_capacity_l * 0.6, expected_life_days=240),
        FilterProfile(purifier_profile_id=profile.id, stage_number=3, stage_name="Reverse Osmosis Membrane", cartridge_type="75 GPD Thin Film Composite", rated_capacity_l=profile.filter_capacity_l, expected_life_days=int(profile.nominal_lifetime_days)),
    ]
    db.add_all(stages)
    db.commit()
    db.refresh(profile)
    return profile

def update_purifier(db: Session, purifier_id: str, data: PurifierUpdate) -> Optional[PurifierProfile]:
    profile = get_purifier_by_id(db, purifier_id)
    if not profile:
        return None

    update_dict = data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)
    return profile

def delete_purifier(db: Session, purifier_id: str) -> bool:
    profile = get_purifier_by_id(db, purifier_id)
    if not profile:
        return False
    db.delete(profile)
    db.commit()
    return True
