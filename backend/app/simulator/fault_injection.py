"""
Fault Injection Module for FilterTwin Virtual Purifier.
Enables controlled injection of physical and sensor anomalies:
- flow_drop: Sudden physical flow restriction or valve clogging
- tds_spike: Sudden membrane seal rupture or bypass
- sensor_disconnection: Intermittent or complete loss of sensor telemetry
- sensor_drift: Accelerated sensor calibration drift
- normal_noise: Pure baseline stochastic fluctuations
- gradual_wear: Standard wear scenario
"""

from enum import Enum
from typing import Optional, Dict, Any

class FaultType(str, Enum):
    NONE = "none"
    FLOW_DROP = "flow_drop"
    TDS_SPIKE = "tds_spike"
    SENSOR_DISCONNECTION = "sensor_disconnection"
    SENSOR_DRIFT = "sensor_drift"
    NORMAL_NOISE = "normal_noise"
    GRADUAL_WEAR = "gradual_wear"

class FaultInjector:
    def __init__(
        self,
        fault_type: FaultType = FaultType.NONE,
        start_day: Optional[float] = None,
        duration_days: Optional[float] = None,
        magnitude: float = 0.5,
    ):
        self.fault_type = fault_type
        self.start_day = start_day
        self.duration_days = duration_days
        self.magnitude = float(magnitude)

    def is_active(self, current_day: float) -> bool:
        if self.fault_type == FaultType.NONE or self.start_day is None:
            return False
        if current_day < self.start_day:
            return False
        if self.duration_days is not None and current_day >= (self.start_day + self.duration_days):
            return False
        return True

    def apply(
        self,
        current_day: float,
        flow_rate: float,
        inlet_tds: float,
        outlet_tds: float,
        rejection_pct: float
    ) -> Dict[str, Any]:
        """
        Applies active fault modifications to observed values.
        Returns modified observations and quality status flag.
        """
        active = self.is_active(current_day)
        sensor_status = "normal"
        
        if not active:
            return {
                "flow_rate": flow_rate,
                "inlet_tds": inlet_tds,
                "outlet_tds": outlet_tds,
                "rejection_pct": rejection_pct,
                "sensor_status": sensor_status,
                "active_fault": FaultType.NONE.value
            }

        # Apply specific fault
        if self.fault_type == FaultType.FLOW_DROP:
            # Drop flow rate by magnitude percentage (e.g. 50% drop)
            drop_factor = max(0.05, 1.0 - self.magnitude)
            flow_rate = flow_rate * drop_factor
            sensor_status = "abrupt_anomaly"

        elif self.fault_type == FaultType.TDS_SPIKE:
            # Outlet TDS spikes sharply toward inlet TDS
            spike = (inlet_tds - outlet_tds) * self.magnitude
            outlet_tds = min(inlet_tds, outlet_tds + spike)
            if inlet_tds > 0:
                rejection_pct = max(0.0, ((inlet_tds - outlet_tds) / inlet_tds) * 100.0)
            sensor_status = "abrupt_anomaly"

        elif self.fault_type == FaultType.SENSOR_DISCONNECTION:
            # Telemetry is missing or NaN
            flow_rate = -1.0  # Sentinel for disconnected / missing
            outlet_tds = -1.0
            rejection_pct = -1.0
            sensor_status = "insufficient_data"

        elif self.fault_type == FaultType.SENSOR_DRIFT:
            # Accelerated drift
            drift_factor = 1.0 + self.magnitude * ((current_day - self.start_day) / 30.0)
            outlet_tds = min(inlet_tds, outlet_tds * drift_factor)
            if inlet_tds > 0:
                rejection_pct = max(0.0, ((inlet_tds - outlet_tds) / inlet_tds) * 100.0)
            sensor_status = "sensor_drift"

        return {
            "flow_rate": flow_rate,
            "inlet_tds": inlet_tds,
            "outlet_tds": outlet_tds,
            "rejection_pct": rejection_pct,
            "sensor_status": sensor_status,
            "active_fault": self.fault_type.value
        }
