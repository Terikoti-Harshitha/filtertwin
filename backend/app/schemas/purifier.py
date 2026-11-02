"""
Pydantic Schemas for Virtual Purifier Profiles.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PurifierCreate(BaseModel):
    name: str = Field(default="Living Room RO Purifier", min_length=2, max_length=100)
    location: str = Field(default="Residential Kitchen")
    initial_inlet_tds: float = Field(default=500.0, ge=50.0, le=2000.0)
    daily_consumption_l: float = Field(default=15.0, ge=1.0, le=100.0)
    initial_flow_rate_lpm: float = Field(default=2.0, ge=0.2, le=5.0)
    filter_capacity_l: float = Field(default=5000.0, ge=500.0, le=20000.0)
    nominal_lifetime_days: float = Field(default=365.0, ge=30.0, le=1000.0)
    degradation_type: str = Field(default="linear")
    degradation_speed: float = Field(default=1.0, ge=0.1, le=5.0)
    sensor_noise: float = Field(default=0.02, ge=0.0, le=0.10)
    sensor_drift: float = Field(default=0.005, ge=0.0, le=0.05)

class PurifierUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    initial_inlet_tds: Optional[float] = None
    daily_consumption_l: Optional[float] = None
    initial_flow_rate_lpm: Optional[float] = None
    filter_capacity_l: Optional[float] = None
    degradation_type: Optional[str] = None
    degradation_speed: Optional[float] = None
    sensor_noise: Optional[float] = None
    sensor_drift: Optional[float] = None

class PurifierResponse(BaseModel):
    id: str
    name: str
    location: str
    installation_date: datetime
    initial_inlet_tds: float
    daily_consumption_l: float
    initial_flow_rate_lpm: float
    filter_capacity_l: float
    nominal_lifetime_days: float
    degradation_type: str
    degradation_speed: float
    sensor_noise: float
    sensor_drift: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
