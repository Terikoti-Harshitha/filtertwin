"""
Ground Truth State Schema and Tracking.
Strict separation of unobservable internal degradation states and true RUL from sensor observations.
Used ONLY by simulation generation and offline evaluation; NEVER exposed to the ML inference pipeline.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass(frozen=True)
class GroundTruthState:
    simulation_run_id: str
    simulated_day: float
    timestamp: str
    degradation_index: float  # D(t) in [0.0, 1.0]
    true_rul_days: float      # Actual remaining days until D(t) == 1.0 or EOL
    true_rul_litres: float    # Actual remaining litres until EOL
    injected_fault_type: str  # Active fault enum value
    is_eol: bool              # True if D(t) >= 1.0
