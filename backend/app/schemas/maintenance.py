"""
Pydantic Schemas for Maintenance Guides, Checklists, and Records.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChecklistStep(BaseModel):
    step_number: int
    title: str
    instruction: str
    required: bool

class GuideResponse(BaseModel):
    id: str
    filter_type: str
    title: str
    description: str
    estimated_minutes: int
    checklist_steps: List[ChecklistStep]

class MaintenanceRecordCreate(BaseModel):
    purifier_profile_id: str
    guide_id: Optional[str] = None
    replacement_type: str = Field(default="RO Membrane")
    technician_notes: Optional[str] = "Routine filter maintenance completed."
    checklist_completed: List[int] = Field(..., description="List of step numbers marked complete")
    reset_baseline_flow: float = Field(default=2.0, ge=0.5, le=5.0)
    reset_baseline_rejection: float = Field(default=96.0, ge=80.0, le=100.0)

class MaintenanceRecordResponse(BaseModel):
    id: str
    purifier_profile_id: str
    guide_id: Optional[str] = None
    replacement_type: str
    completed_at: datetime
    technician_notes: Optional[str] = None
    checklist_completed_json: Any
    reset_baseline_flow: float
    reset_baseline_rejection: float

    class Config:
        from_attributes = True
