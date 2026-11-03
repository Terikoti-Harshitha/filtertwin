import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "FilterTwin"

def test_purifier_crud_endpoints():
    # 1. List
    res = client.get("/api/v1/purifiers")
    assert res.status_code == 200
    initial_count = len(res.json())

    # 2. Create
    payload = {
        "name": "Test Office Purifier",
        "location": "Breakroom",
        "initial_inlet_tds": 450.0,
        "daily_consumption_l": 25.0,
        "initial_flow_rate_lpm": 2.2,
        "filter_capacity_l": 6000.0,
        "nominal_lifetime_days": 300.0,
        "degradation_type": "exponential",
        "degradation_speed": 1.2,
        "sensor_noise": 0.015,
        "sensor_drift": 0.003,
    }
    create_res = client.post("/api/v1/purifiers", json=payload)
    assert create_res.status_code == 201
    created_purifier = create_res.json()
    purifier_id = created_purifier["id"]
    assert created_purifier["name"] == "Test Office Purifier"

    # 3. Get single
    get_res = client.get(f"/api/v1/purifiers/{purifier_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == purifier_id

    # 4. Update
    put_res = client.put(f"/api/v1/purifiers/{purifier_id}", json={"name": "Updated Office Purifier"})
    assert put_res.status_code == 200
    assert put_res.json()["name"] == "Updated Office Purifier"

    # 5. Delete
    del_res = client.delete(f"/api/v1/purifiers/{purifier_id}")
    assert del_res.status_code == 204

def test_simulation_and_diagnostic_flow():
    # Create purifier for simulation
    p_res = client.post("/api/v1/purifiers", json={
        "name": "Diagnostic Test Purifier",
        "initial_inlet_tds": 500.0,
        "daily_consumption_l": 15.0,
        "initial_flow_rate_lpm": 2.0,
        "filter_capacity_l": 5000.0,
    })
    purifier_id = p_res.json()["id"]

    # Start simulation
    sim_res = client.post("/api/v1/simulations", json={
        "purifier_profile_id": purifier_id,
        "degradation_type": "linear",
        "fault_type": "none",
        "random_seed": 77,
        "duration_days": 45.0,
    })
    assert sim_res.status_code == 201
    sim_data = sim_res.json()
    sim_id = sim_data["id"]

    # Fetch readings
    readings_res = client.get(f"/api/v1/simulations/{sim_id}/readings")
    assert readings_res.status_code == 200
    readings = readings_res.json()
    assert len(readings) == 45
    assert readings[0]["flow_rate_lpm"] is not None

    # Run diagnostic prediction
    diag_res = client.post(f"/api/v1/diagnostics/{sim_id}/predict")
    assert diag_res.status_code == 200
    diag = diag_res.json()
    assert "baseline_prediction" in diag
    assert "linear_prediction" in diag
    assert "uncertainty_interval" in diag
    assert "diagnosis" in diag
    assert "explanation" in diag

    # Inject fault
    fault_res = client.post(f"/api/v1/simulations/{sim_id}/inject-fault", json={
        "fault_type": "flow_drop",
        "start_day": 30.0,
        "magnitude": 0.6,
    })
    assert fault_res.status_code == 200

def test_evaluations_and_maintenance():
    # Evaluations latest
    eval_res = client.get("/api/v1/evaluations/latest")
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert "regression_comparison" in eval_data
    assert "anomaly_detection" in eval_data

    # Download CSV report
    csv_res = client.get("/api/v1/evaluations/report/csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "Fixed-Volume Baseline" in csv_res.text

    # Guides
    guides_res = client.get("/api/v1/maintenance/guides")
    assert guides_res.status_code == 200
    assert len(guides_res.json()) >= 1

    # Models
    models_res = client.get("/api/v1/models")
    assert models_res.status_code == 200
    assert len(models_res.json()) >= 3

def test_wokwi_telemetry_ingestion():
    # Ingest virtual ESP32 sensor reading
    payload = {
        "device_id": "wokwi-esp32-unit-test",
        "flow_rate_lpm": 1.85,
        "inlet_tds_ppm": 520.0,
        "outlet_tds_ppm": 45.0,
        "rejection_percentage": 91.3,
        "cumulative_volume_l": 500.0,
        "sensor_status": "normal",
    }
    res = client.post("/api/v1/telemetry/ingest", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "ingested"
    assert data["device_id"] == "wokwi-esp32-unit-test"
    assert data["flow_rate_lpm"] == 1.85
    assert data["rejection_percentage"] == 91.3
