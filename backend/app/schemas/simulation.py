"""
Pydantic Schemas for Simulation Execution and Telemetry Readings.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class SimulationCreate(BaseModel):
    purifier_profile_id: str
    degradation_type: str = Field(default="linear")
    degradation_speed: float = Field(default=1.0, ge=0.1, le=5.0)
    fault_type: str = Field(default="none")
    fault_day: Optional[float] = None
    fault_magnitude: float = Field(default=0.5, ge=0.1, le=1.0)
    random_seed: int = Field(default=42)
    duration_days: float = Field(default=90.0, ge=5.0, le=730.0)

class FaultInjectRequest(BaseModel):
    fault_type: str
    start_day: float
    magnitude: float = Field(default=0.5, ge=0.1, le=1.0)

class ReadingResponse(BaseModel):
    id: Optional[int] = None
    simulation_run_id: str
    timestamp: str
    simulated_day: float
    cumulative_volume_l: float
    flow_rate_lpm: Optional[float] = None
    inlet_tds_ppm: Optional[float] = None
    outlet_tds_ppm: Optional[float] = None
    rejection_percentage: Optional[float] = None
    sensor_status: str

    class Config:
        from_attributes = True

class GroundTruthResponse(BaseModel):
    simulation_run_id: str
    timestamp: str
    simulated_day: float
    degradation_index: float
    true_rul_days: float
    true_rul_litres: float
    injected_fault_type: str
    is_eol: bool

    class Config:
        from_attributes = True

class SimulationResponse(BaseModel):
    id: str
    purifier_profile_id: str
    status: str
    degradation_type: str
    fault_type: str
    fault_day: Optional[float] = None
    fault_magnitude: float
    random_seed: int
    duration_days: float
    current_day: float
    cumulative_volume_l: float
    created_at: datetime
    latest_reading: Optional[ReadingResponse] = None

    class Config:
        from_attributes = True
