import pytest
import numpy as np
from app.simulator.degradation import DegradationModel, DegradationType
from app.simulator.sensor_models import SensorModel
from app.simulator.fault_injection import FaultInjector, FaultType
from app.simulator.engine import PurifierSimulator

def test_linear_degradation():
    model = DegradationModel(model_type=DegradationType.LINEAR, nominal_lifetime_days=100.0)
    assert model.compute(0.0) == 0.0
    assert pytest.approx(model.compute(50.0), 0.01) == 0.5
    assert model.compute(100.0) == 1.0
    assert model.compute(150.0) == 1.0  # Clamped to 1.0

def test_exponential_degradation():
    model = DegradationModel(model_type=DegradationType.EXPONENTIAL, nominal_lifetime_days=100.0, rate_k=0.02)
    d0 = model.compute(0.0)
    d50 = model.compute(50.0)
    d100 = model.compute(100.0)
    assert d0 == 0.0
    assert 0.0 < d50 < 1.0
    assert pytest.approx(d100, 0.01) == 1.0
    # Exponential should start slower than linear
    assert d50 < 0.5

def test_nonlinear_degradation():
    model = DegradationModel(model_type=DegradationType.NONLINEAR, nominal_lifetime_days=100.0, power_p=2.0)
    assert model.compute(0.0) == 0.0
    assert pytest.approx(model.compute(50.0), 0.01) == 0.25  # (0.5)^2
    assert pytest.approx(model.compute(100.0), 0.01) == 1.0

def test_abrupt_fault_degradation():
    model = DegradationModel(model_type=DegradationType.ABRUPT, nominal_lifetime_days=100.0, abrupt_time=40.0, abrupt_delta=0.4)
    assert pytest.approx(model.compute(39.0), 0.01) == 0.39
    assert pytest.approx(model.compute(40.0), 0.01) == 0.80  # 0.40 + 0.40
    assert model.solve_eol_time() <= 100.0

def test_sensor_bounds_and_drift():
    rng = np.random.default_rng(123)
    sensor = SensorModel(initial_flow_rate_lpm=2.0, noise_level=0.01, drift_rate=0.01, rng=rng)
    flow, noise = sensor.generate_flow_rate(degradation=0.5, simulated_day=50.0)
    assert flow > 0.0
    tds_out, r, rej_pct = sensor.generate_tds_readings(inlet_tds_ppm=600.0, degradation=0.5, simulated_day=50.0)
    assert tds_out >= 0.0
    assert tds_out <= 600.0
    assert 0.0 <= rej_pct <= 100.0

def test_fault_injection_flow_drop():
    injector = FaultInjector(fault_type=FaultType.FLOW_DROP, start_day=20.0, magnitude=0.6)
    assert not injector.is_active(19.0)
    assert injector.is_active(20.0)
    res = injector.apply(20.0, flow_rate=2.0, inlet_tds=500.0, outlet_tds=50.0, rejection_pct=90.0)
    assert res["flow_rate"] < 1.0  # 2.0 * (1 - 0.6) = 0.8
    assert res["sensor_status"] == "abrupt_anomaly"

def test_simulator_engine_reproducibility():
    sim1 = PurifierSimulator(random_seed=999)
    obs1, gt1 = sim1.run_simulation(duration_days=30.0)

    sim2 = PurifierSimulator(random_seed=999)
    obs2, gt2 = sim2.run_simulation(duration_days=30.0)

    assert len(obs1) == 30
    assert len(gt1) == 30
    assert obs1[15]["flow_rate_lpm"] == obs2[15]["flow_rate_lpm"]
    assert obs1[15]["outlet_tds_ppm"] == obs2[15]["outlet_tds_ppm"]
    assert gt1[15].degradation_index == gt2[15].degradation_index

def test_strict_separation_no_data_leakage():
    sim = PurifierSimulator(random_seed=42)
    obs, gt = sim.step()
    # Check that observed dictionary does NOT have degradation index or true RUL
    assert "degradation_index" not in obs
    assert "true_rul_days" not in obs
    assert "true_rul_litres" not in obs
    assert "is_eol" not in obs
    # Ground truth state holds them
    assert hasattr(gt, "degradation_index")
    assert hasattr(gt, "true_rul_days")
