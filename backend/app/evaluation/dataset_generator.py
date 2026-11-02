"""
Evaluation Dataset Generator.
Generates comprehensive simulation runs across diverse operating conditions,
degradation profiles, and fault scenarios for model training and held-out evaluation.
"""

import numpy as np
from typing import List, Dict, Any, Tuple

from app.simulator.engine import PurifierSimulator
from app.simulator.ground_truth import GroundTruthState

def generate_scenario(
    scenario_id: str,
    seed: int,
    degradation_type: str = "linear",
    inlet_tds: float = 500.0,
    daily_consumption: float = 15.0,
    filter_capacity: float = 5000.0,
    sensor_noise: float = 0.02,
    sensor_drift: float = 0.005,
    fault_type: str = "none",
    fault_day: float = 40.0,
    fault_magnitude: float = 0.5,
    duration_days: float = 120.0,
) -> Tuple[List[Dict[str, Any]], List[GroundTruthState]]:
    """
    Generates a single deterministic simulation scenario.
    Returns (observed_readings, ground_truth_states).
    """
    sim = PurifierSimulator(
        simulation_run_id=scenario_id,
        initial_inlet_tds=inlet_tds,
        daily_consumption_l=daily_consumption,
        initial_flow_rate_lpm=2.0,
        filter_capacity_l=filter_capacity,
        degradation_type=degradation_type,
        sensor_noise=sensor_noise,
        sensor_drift=sensor_drift,
        fault_type=fault_type,
        fault_day=fault_day if fault_type != "none" else None,
        fault_magnitude=fault_magnitude,
        random_seed=seed,
    )
    return sim.run_simulation(duration_days=duration_days)

def generate_dataset_suite(
    num_scenarios: int = 200,
    base_seed: int = 1000,
    degradation_types: List[str] = None,
    include_faults: bool = True
) -> List[Dict[str, Any]]:
    """
    Generates a suite of diverse scenarios with varied operational parameters.
    """
    if degradation_types is None:
        degradation_types = ["linear", "exponential", "nonlinear", "abrupt"]

    fault_types = ["none", "flow_drop", "tds_spike", "sensor_disconnection", "sensor_drift"] if include_faults else ["none"]

    rng = np.random.default_rng(base_seed)
    suite = []

    for i in range(num_scenarios):
        sc_id = f"scenario-{i+1:04d}"
        seed = int(rng.integers(1, 1000000))
        deg_type = rng.choice(degradation_types)
        f_type = rng.choice(fault_types) if include_faults else "none"

        inlet_tds = float(rng.uniform(250.0, 850.0))
        daily_vol = float(rng.uniform(10.0, 30.0))
        capacity = float(rng.uniform(3500.0, 6500.0))
        noise = float(rng.uniform(0.01, 0.035))
        drift = float(rng.uniform(0.002, 0.008))
        f_day = float(rng.uniform(25.0, 85.0))
        f_mag = float(rng.uniform(0.35, 0.65))

        obs, gt = generate_scenario(
            scenario_id=sc_id,
            seed=seed,
            degradation_type=deg_type,
            inlet_tds=inlet_tds,
            daily_consumption=daily_vol,
            filter_capacity=capacity,
            sensor_noise=noise,
            sensor_drift=drift,
            fault_type=f_type,
            fault_day=f_day,
            fault_magnitude=f_mag,
            duration_days=100.0,
        )

        suite.append({
            "scenario_id": sc_id,
            "seed": seed,
            "degradation_type": deg_type,
            "injected_fault_type": f_type,
            "inlet_tds": inlet_tds,
            "daily_consumption": daily_vol,
            "filter_capacity": capacity,
            "observations": obs,
            "ground_truth": gt,
        })

    return suite
