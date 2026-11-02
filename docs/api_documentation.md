# FilterTwin REST API Documentation

Base URI: `/api/v1`

Interactive API Docs:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 1. Purifiers

### `GET /api/v1/purifiers`
List all registered virtual purifier configurations.

### `POST /api/v1/purifiers`
Create a new virtual purifier configuration.
```json
{
  "name": "Kitchen RO Purifier",
  "location": "Residential Kitchen",
  "initial_inlet_tds": 500.0,
  "daily_consumption_l": 15.0,
  "initial_flow_rate_lpm": 2.0,
  "filter_capacity_l": 5000.0,
  "nominal_lifetime_days": 365.0,
  "degradation_type": "linear",
  "degradation_speed": 1.0,
  "sensor_noise": 0.02,
  "sensor_drift": 0.005
}
```

### `GET /api/v1/purifiers/{id}`
Retrieve a specific purifier profile.

### `PUT /api/v1/purifiers/{id}`
Update operational settings.

### `DELETE /api/v1/purifiers/{id}`
Delete a purifier profile and cascade simulation data.

---

## 2. Simulations

### `POST /api/v1/simulations`
Run a simulation batch for a purifier.
```json
{
  "purifier_profile_id": "uuid-here",
  "degradation_type": "linear",
  "fault_type": "none",
  "random_seed": 42,
  "duration_days": 90.0
}
```

### `GET /api/v1/simulations/{id}`
Get execution state and latest reading.

### `GET /api/v1/simulations/{id}/readings`
Fetch time-series sensor observations.
Query params: `limit` (int, optional).

### `GET /api/v1/simulations/{id}/ground-truth`
*Restricted Evaluation Endpoint.* Access hidden degradation indices and true EOL days.

### `POST /api/v1/simulations/{id}/inject-fault`
```json
{
  "fault_type": "flow_drop",
  "start_day": 30.0,
  "magnitude": 0.5
}
```

---

## 3. Diagnostics & Predictions

### `POST /api/v1/diagnostics/{simulation_id}/predict`
Compute full real-time diagnostics:
```json
{
  "simulation_id": "sim-uuid",
  "simulated_day": 45.0,
  "data_quality_status": "GOOD",
  "baseline_prediction": {
    "model_version": "fixed-volume-baseline-v1",
    "rul_days": 105.0,
    "rul_litres": 1575.0,
    "is_adaptive": false
  },
  "linear_prediction": {
    "model_version": "linear-regression-v1",
    "rul_days": 68.4,
    "rul_litres": 1026.0,
    "is_adaptive": true
  },
  "gradient_boosting_prediction": {
    "model_version": "gradient-boosting-v1",
    "rul_days": 65.1,
    "rul_litres": 976.5,
    "is_adaptive": true
  },
  "uncertainty_interval": {
    "rul_median_days": 66.0,
    "rul_lower_days": 54.0,
    "rul_upper_days": 79.0,
    "interval_width_days": 25.0,
    "nominal_coverage_pct": 80.0
  },
  "diagnosis": {
    "category": "NORMAL",
    "subtype": "none",
    "severity": "LOW"
  },
  "explanation": {
    "recommended_action": "CONTINUE_NORMAL_OPERATION",
    "contributing_factors": []
  }
}
```

### `GET /api/v1/diagnostics/{simulation_id}/alerts`
List triggered alerts.

---

## 4. Evaluations

### `GET /api/v1/evaluations/latest`
Fetch latest 200-scenario benchmark results.

### `POST /api/v1/evaluations`
Run a live evaluation benchmark:
```json
{
  "num_scenarios": 200,
  "include_faults": true
}
```

### `GET /api/v1/evaluations/report/csv`
Download CSV benchmark summary report.

---

## 5. Maintenance

### `GET /api/v1/maintenance/guides`
Retrieve standard manufacturer procedures.

### `POST /api/v1/maintenance/records`
Sign off on completed checklist and reset baseline.
```json
{
  "purifier_profile_id": "uuid-here",
  "guide_id": "guide-ro-membrane",
  "replacement_type": "RO Membrane",
  "technician_notes": "Cartridge replaced and lines purged.",
  "checklist_completed": [1, 2, 3, 4, 5, 6, 7, 8],
  "reset_baseline_flow": 2.1,
  "reset_baseline_rejection": 96.5
}
```
