"""
Relational Database Entities for FilterTwin.
Implements the 12 core tables:
- purifier_profiles, filter_profiles
- simulation_runs, sensor_readings, ground_truth_states
- model_versions, predictions, diagnostic_alerts
- maintenance_guides, maintenance_records
- evaluation_runs, evaluation_metrics
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import relationship

from app.database.base import Base

def gen_uuid():
    return str(uuid.uuid4())

class PurifierProfile(Base):
    __tablename__ = "purifier_profiles"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(100), nullable=False, default="Living Room RO Purifier")
    location = Column(String(100), default="Residential Kitchen")
    installation_date = Column(DateTime, default=datetime.utcnow)
    initial_inlet_tds = Column(Float, default=500.0)
    daily_consumption_l = Column(Float, default=15.0)
    initial_flow_rate_lpm = Column(Float, default=2.0)
    filter_capacity_l = Column(Float, default=5000.0)
    nominal_lifetime_days = Column(Float, default=365.0)
    degradation_type = Column(String(50), default="linear")
    degradation_speed = Column(Float, default=1.0)
    sensor_noise = Column(Float, default=0.02)
    sensor_drift = Column(Float, default=0.005)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    filters = relationship("FilterProfile", back_populates="purifier", cascade="all, delete-orphan")
    simulations = relationship("SimulationRun", back_populates="purifier", cascade="all, delete-orphan")
    maintenance_records = relationship("MaintenanceRecord", back_populates="purifier", cascade="all, delete-orphan")

class FilterProfile(Base):
    __tablename__ = "filter_profiles"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    purifier_profile_id = Column(String(36), ForeignKey("purifier_profiles.id"), nullable=False)
    stage_number = Column(Integer, default=1)
    stage_name = Column(String(100), default="RO Membrane")
    cartridge_type = Column(String(100), default="Thin Film Composite (TFC)")
    rated_capacity_l = Column(Float, default=5000.0)
    expected_life_days = Column(Integer, default=365)

    purifier = relationship("PurifierProfile", back_populates="filters")

class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    purifier_profile_id = Column(String(36), ForeignKey("purifier_profiles.id"), nullable=False)
    status = Column(String(50), default="running") # idle, running, paused, completed
    degradation_type = Column(String(50), default="linear")
    fault_type = Column(String(50), default="none")
    fault_day = Column(Float, nullable=True)
    fault_magnitude = Column(Float, default=0.5)
    random_seed = Column(Integer, default=42)
    duration_days = Column(Float, default=120.0)
    current_day = Column(Float, default=0.0)
    cumulative_volume_l = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    purifier = relationship("PurifierProfile", back_populates="simulations")
    readings = relationship("SensorReading", back_populates="simulation", cascade="all, delete-orphan")
    ground_truths = relationship("GroundTruthStateEntity", back_populates="simulation", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="simulation", cascade="all, delete-orphan")
    alerts = relationship("DiagnosticAlert", back_populates="simulation", cascade="all, delete-orphan")

class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    simulation_run_id = Column(String(36), ForeignKey("simulation_runs.id"), nullable=False)
    timestamp = Column(String(50), nullable=False)
    simulated_day = Column(Float, nullable=False)
    cumulative_volume_l = Column(Float, nullable=False)
    flow_rate_lpm = Column(Float, nullable=True)
    inlet_tds_ppm = Column(Float, nullable=True)
    outlet_tds_ppm = Column(Float, nullable=True)
    rejection_percentage = Column(Float, nullable=True)
    sensor_status = Column(String(50), default="normal")
    created_at = Column(DateTime, default=datetime.utcnow)

    simulation = relationship("SimulationRun", back_populates="readings")

class GroundTruthStateEntity(Base):
    __tablename__ = "ground_truth_states"

    id = Column(Integer, primary_key=True, autoincrement=True)
    simulation_run_id = Column(String(36), ForeignKey("simulation_runs.id"), nullable=False)
    timestamp = Column(String(50), nullable=False)
    simulated_day = Column(Float, nullable=False)
    degradation_index = Column(Float, nullable=False)
    true_rul_days = Column(Float, nullable=False)
    true_rul_litres = Column(Float, nullable=False)
    injected_fault_type = Column(String(50), default="none")
    is_eol = Column(Boolean, default=False)

    simulation = relationship("SimulationRun", back_populates="ground_truths")

class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    model_name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    algorithm = Column(String(100), nullable=False)
    training_date = Column(DateTime, default=datetime.utcnow)
    mae_score = Column(Float, nullable=True)
    rmse_score = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    simulation_run_id = Column(String(36), ForeignKey("simulation_runs.id"), nullable=False)
    model_version = Column(String(50), default="linear-regression-v1")
    timestamp = Column(String(50), nullable=False)
    rul_median_days = Column(Float, nullable=False)
    rul_lower_days = Column(Float, nullable=True)
    rul_upper_days = Column(Float, nullable=True)
    rul_median_litres = Column(Float, nullable=True)
    diagnostic_category = Column(String(50), default="NORMAL")
    diagnostic_subtype = Column(String(50), default="none")
    quality_status = Column(String(50), default="GOOD")
    recommended_action = Column(String(100), default="CONTINUE_NORMAL_OPERATION")
    feature_contributions_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    simulation = relationship("SimulationRun", back_populates="predictions")

class DiagnosticAlert(Base):
    __tablename__ = "diagnostic_alerts"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    simulation_run_id = Column(String(36), ForeignKey("simulation_runs.id"), nullable=False)
    timestamp = Column(String(50), nullable=False)
    simulated_day = Column(Float, default=0.0)
    category = Column(String(50), nullable=False)
    subtype = Column(String(50), default="none")
    severity = Column(String(20), default="LOW") # LOW, MEDIUM, HIGH, CRITICAL
    message = Column(Text, nullable=False)
    evidence_json = Column(JSON, nullable=True)
    is_acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    simulation = relationship("SimulationRun", back_populates="alerts")

class MaintenanceGuide(Base):
    __tablename__ = "maintenance_guides"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    filter_type = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    estimated_minutes = Column(Integer, default=20)
    checklist_steps_json = Column(JSON, nullable=False)

class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    purifier_profile_id = Column(String(36), ForeignKey("purifier_profiles.id"), nullable=False)
    guide_id = Column(String(36), nullable=True)
    replacement_type = Column(String(100), default="RO Membrane")
    completed_at = Column(DateTime, default=datetime.utcnow)
    technician_notes = Column(Text, nullable=True)
    checklist_completed_json = Column(JSON, nullable=False)
    reset_baseline_flow = Column(Float, default=2.0)
    reset_baseline_rejection = Column(Float, default=95.0)

    purifier = relationship("PurifierProfile", back_populates="maintenance_records")

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    timestamp = Column(DateTime, default=datetime.utcnow)
    total_scenarios = Column(Integer, default=200)
    total_checkpoints = Column(Integer, default=1000)
    execution_time_seconds = Column(Float, default=0.0)
    summary_metrics_json = Column(JSON, nullable=False)
