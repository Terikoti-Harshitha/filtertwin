"""
Simulation Orchestration Service.
Coordinates PurifierSimulator instances, executes time steps, persists time-series readings
and ground truth records in database.
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple

from app.models.entities import SimulationRun, SensorReading, GroundTruthStateEntity, PurifierProfile
from app.schemas.simulation import SimulationCreate, FaultInjectRequest
from app.simulator.engine import PurifierSimulator

def create_and_run_simulation(
    db: Session,
    purifier: PurifierProfile,
    data: SimulationCreate
) -> Tuple[SimulationRun, List[SensorReading]]:
    """
    Creates a new simulation run and executes the initial scenario batch.
    """
    run = SimulationRun(
        purifier_profile_id=purifier.id,
        status="running",
        degradation_type=data.degradation_type,
        fault_type=data.fault_type,
        fault_day=data.fault_day,
        fault_magnitude=data.fault_magnitude,
        random_seed=data.random_seed,
        duration_days=data.duration_days,
        current_day=0.0,
        cumulative_volume_l=0.0,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Instantiate simulator
    sim = PurifierSimulator(
        simulation_run_id=run.id,
        initial_inlet_tds=purifier.initial_inlet_tds,
        daily_consumption_l=purifier.daily_consumption_l,
        initial_flow_rate_lpm=purifier.initial_flow_rate_lpm,
        filter_capacity_l=purifier.filter_capacity_l,
        nominal_lifetime_days=purifier.nominal_lifetime_days,
        degradation_type=data.degradation_type,
        degradation_speed=data.degradation_speed,
        sensor_noise=purifier.sensor_noise,
        sensor_drift=purifier.sensor_drift,
        fault_type=data.fault_type,
        fault_day=data.fault_day,
        fault_magnitude=data.fault_magnitude,
        random_seed=data.random_seed,
    )

    obs_list, gt_list = sim.run_simulation(duration_days=data.duration_days, time_step_days=1.0)

    reading_entities = []
    for obs in obs_list:
        reading = SensorReading(
            simulation_run_id=run.id,
            timestamp=obs["timestamp"],
            simulated_day=obs["simulated_day"],
            cumulative_volume_l=obs["cumulative_volume_l"],
            flow_rate_lpm=obs["flow_rate_lpm"],
            inlet_tds_ppm=obs["inlet_tds_ppm"],
            outlet_tds_ppm=obs["outlet_tds_ppm"],
            rejection_percentage=obs["rejection_percentage"],
            sensor_status=obs["sensor_status"],
        )
        reading_entities.append(reading)

    gt_entities = []
    for gt in gt_list:
        gt_e = GroundTruthStateEntity(
            simulation_run_id=run.id,
            timestamp=gt.timestamp,
            simulated_day=gt.simulated_day,
            degradation_index=gt.degradation_index,
            true_rul_days=gt.true_rul_days,
            true_rul_litres=gt.true_rul_litres,
            injected_fault_type=gt.injected_fault_type,
            is_eol=gt.is_eol,
        )
        gt_entities.append(gt_e)

    db.add_all(reading_entities)
    db.add_all(gt_entities)

    # Update run state
    if obs_list:
        last = obs_list[-1]
        run.current_day = last["simulated_day"]
        run.cumulative_volume_l = last["cumulative_volume_l"]
        run.status = "completed" if run.current_day >= run.duration_days else "running"

    db.commit()
    db.refresh(run)

    return run, reading_entities

def get_simulation_by_id(db: Session, sim_id: str) -> Optional[SimulationRun]:
    return db.query(SimulationRun).filter(SimulationRun.id == sim_id).first()

def get_simulations_for_purifier(db: Session, purifier_id: str) -> List[SimulationRun]:
    return db.query(SimulationRun).filter(SimulationRun.purifier_profile_id == purifier_id).order_by(SimulationRun.created_at.desc()).all()

def get_readings_for_simulation(db: Session, sim_id: str, limit: Optional[int] = None) -> List[SensorReading]:
    q = db.query(SensorReading).filter(SensorReading.simulation_run_id == sim_id).order_by(SensorReading.simulated_day.asc())
    if limit is not None:
        q = q.limit(limit)
    return q.all()

def get_ground_truth_for_simulation(db: Session, sim_id: str) -> List[GroundTruthStateEntity]:
    return db.query(GroundTruthStateEntity).filter(GroundTruthStateEntity.simulation_run_id == sim_id).order_by(GroundTruthStateEntity.simulated_day.asc()).all()

def inject_fault_into_simulation(db: Session, sim_id: str, fault_data: FaultInjectRequest) -> bool:
    run = get_simulation_by_id(db, sim_id)
    if not run:
        return False
    run.fault_type = fault_data.fault_type
    run.fault_day = fault_data.start_day
    run.fault_magnitude = fault_data.magnitude
    db.commit()
    return True
