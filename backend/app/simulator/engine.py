"""
Virtual Water Purifier Simulator Engine.
Orchestrates degradation laws, sensor physics, noise, drift, and fault injection.
Ensures strict separation between observed telemetry and unobserved ground-truth state.
"""

import uuid
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional

from app.simulator.degradation import DegradationModel, DegradationType
from app.simulator.sensor_models import SensorModel
from app.simulator.fault_injection import FaultInjector, FaultType
from app.simulator.ground_truth import GroundTruthState

class PurifierSimulator:
    def __init__(
        self,
        simulation_run_id: Optional[str] = None,
        initial_inlet_tds: float = 500.0,
        daily_consumption_l: float = 15.0,
        initial_flow_rate_lpm: float = 2.0,
        filter_capacity_l: float = 5000.0,
        nominal_lifetime_days: float = 365.0,
        degradation_type: str = "linear",
        degradation_speed: float = 1.0,
        power_p: float = 1.8,
        rate_k: float = 0.015,
        sensor_noise: float = 0.02,
        sensor_drift: float = 0.005,
        fault_type: str = "none",
        fault_day: Optional[float] = None,
        fault_magnitude: float = 0.5,
        missing_data_pct: float = 0.0,
        random_seed: int = 42,
        start_datetime: Optional[datetime] = None,
    ):
        self.simulation_run_id = simulation_run_id or str(uuid.uuid4())
        self.inlet_tds = float(initial_inlet_tds)
        self.daily_consumption = max(0.1, float(daily_consumption_l))
        self.initial_flow = max(0.1, float(initial_flow_rate_lpm))
        self.capacity_l = max(100.0, float(filter_capacity_l))
        self.nominal_lifetime_days = max(10.0, float(nominal_lifetime_days) / max(0.1, degradation_speed))
        self.degradation_type = DegradationType(degradation_type)
        self.missing_data_pct = float(missing_data_pct)
        self.random_seed = int(random_seed)
        self.start_datetime = start_datetime or datetime(2026, 1, 1, 9, 0, 0)

        # PRNG
        self.rng = np.random.default_rng(self.random_seed)

        # Degradation model
        self.deg_model = DegradationModel(
            model_type=self.degradation_type,
            nominal_lifetime_days=self.nominal_lifetime_days,
            rate_k=rate_k,
            power_p=power_p,
            abrupt_time=fault_day if self.degradation_type == DegradationType.ABRUPT else None,
            abrupt_delta=fault_magnitude,
        )

        # Sensor physics
        self.sensor_model = SensorModel(
            initial_flow_rate_lpm=self.initial_flow,
            flow_alpha=0.55,
            initial_rejection_ratio=0.96,
            rejection_beta=0.35,
            noise_level=sensor_noise,
            drift_rate=sensor_drift,
            rng=self.rng,
        )

        # Fault injector
        self.fault_injector = FaultInjector(
            fault_type=FaultType(fault_type),
            start_day=fault_day,
            duration_days=None,
            magnitude=fault_magnitude,
        )

        # Dynamic State tracking
        self.current_day = 0.0
        self.cumulative_volume = 0.0
        self.eol_day = self.deg_model.solve_eol_time()

    def step(self, time_step_days: float = 1.0) -> Tuple[Dict[str, Any], GroundTruthState]:
        """
        Advance simulation by time_step_days.
        Returns (observed_reading_dict, ground_truth_state_obj).
        """
        sim_day = self.current_day
        ts = (self.start_datetime + timedelta(days=sim_day)).isoformat()

        # 1. Hidden degradation state
        deg = self.deg_model.compute(sim_day)
        is_eol = bool(deg >= 1.0)

        # True RUL calculations
        true_rul_days = max(0.0, self.eol_day - sim_day)
        true_rul_litres = max(0.0, true_rul_days * self.daily_consumption)

        active_fault_name = self.fault_injector.fault_type.value if self.fault_injector.is_active(sim_day) else "none"

        ground_truth = GroundTruthState(
            simulation_run_id=self.simulation_run_id,
            simulated_day=sim_day,
            timestamp=ts,
            degradation_index=deg,
            true_rul_days=true_rul_days,
            true_rul_litres=true_rul_litres,
            injected_fault_type=active_fault_name,
            is_eol=is_eol,
        )

        # 2. Physics & Sensor generation
        # Inlet TDS can have slight natural water supply variability (+/- 3%)
        inlet_var = self.inlet_tds * (1.0 + self.rng.normal(0.0, 0.02))
        inlet_var = max(50.0, inlet_var)

        flow_lpm, _ = self.sensor_model.generate_flow_rate(deg, sim_day)
        outlet_tds, _, rejection_pct = self.sensor_model.generate_tds_readings(inlet_var, deg, sim_day)

        # 3. Apply active fault modifications
        fault_applied = self.fault_injector.apply(
            current_day=sim_day,
            flow_rate=flow_lpm,
            inlet_tds=inlet_var,
            outlet_tds=outlet_tds,
            rejection_pct=rejection_pct,
        )

        flow_observed = fault_applied["flow_rate"]
        inlet_observed = fault_applied["inlet_tds"]
        outlet_observed = fault_applied["outlet_tds"]
        rejection_observed = fault_applied["rejection_pct"]
        sensor_status = fault_applied["sensor_status"]

        # Missing data injection (simulating random dropouts)
        if self.missing_data_pct > 0 and self.rng.random() < self.missing_data_pct:
            flow_observed = None
            outlet_observed = None
            rejection_observed = None
            sensor_status = "insufficient_data"

        # Update cumulative volume (based on actual flow or daily consumption)
        # 1 day usage: daily_consumption L
        step_volume = self.daily_consumption * time_step_days
        self.cumulative_volume += step_volume
        self.current_day += time_step_days

        observed_reading = {
            "simulation_run_id": self.simulation_run_id,
            "timestamp": ts,
            "simulated_day": round(sim_day, 2),
            "cumulative_volume_l": round(self.cumulative_volume, 2),
            "flow_rate_lpm": round(flow_observed, 3) if flow_observed is not None and flow_observed >= 0 else None,
            "inlet_tds_ppm": round(inlet_observed, 1) if inlet_observed is not None and inlet_observed >= 0 else None,
            "outlet_tds_ppm": round(outlet_observed, 1) if outlet_observed is not None and outlet_observed >= 0 else None,
            "rejection_percentage": round(rejection_observed, 2) if rejection_observed is not None and rejection_observed >= 0 else None,
            "sensor_status": sensor_status,
        }

        return observed_reading, ground_truth

    def run_simulation(
        self,
        duration_days: float = 180.0,
        time_step_days: float = 1.0,
    ) -> Tuple[List[Dict[str, Any]], List[GroundTruthState]]:
        """
        Runs a complete scenario and returns lists of observed readings and ground truth states.
        """
        readings: List[Dict[str, Any]] = []
        ground_truths: List[GroundTruthState] = []

        steps = int(duration_days / time_step_days)
        for _ in range(steps):
            obs, gt = self.step(time_step_days)
            readings.append(obs)
            ground_truths.append(gt)

        return readings, ground_truths
