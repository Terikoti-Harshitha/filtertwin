# FilterTwin System Architecture

## Overview
FilterTwin is an uncertainty-aware, simulation-driven predictive maintenance platform for water purifier filters. It is designed using a modular 6-layer architecture that completely isolates physics simulation, predictive machine learning, and persistence from presentation components.

```
+-------------------------------------------------------------------+
|                    Layer 1: Presentation Layer                    |
|   React 18 + Vite + Tailwind CSS + Recharts + Lucide-React        |
|   (Dashboard, Simulator Studio, Monitoring, Diagnostics, Eval)   |
+---------------------------------+---------------------------------+
                                  | REST API (/api/v1)
+---------------------------------v---------------------------------+
|               Layer 2: API & Application Services                 |
|       FastAPI + Pydantic v2 + Dependency Injection + CORS         |
+---------------------------------+---------------------------------+
                                  |
         +------------------------+------------------------+
         |                                                 |
+--------v------------------------+      +-----------------v--------+
|   Layer 3: Simulation Engine    |      | Layer 4: Intelligence    |
| - Degradation Models            |      | - Feature Engineering    |
|   (Linear, Exp, Nonlinear, Jump)|      | - Fixed-Volume Baseline  |
| - Hydraulic & Solute Physics    |      | - Ridge Linear Regression|
| - Sensor Noise & Drift Models   |      | - Gradient Boosted Trees |
| - Fault Injection (5 Scenarios) |      | - Quantile Intervals     |
| - Ground Truth (Segregated)     |      | - Anomaly Classification |
+--------+------------------------+      | - Explainability Engine  |
         |                               +-----------------+--------+
         |                                                 |
+--------v-------------------------------------------------v--------+
|                   Layer 5: Evaluation Framework                   |
| - 200+ Held-out Scenarios across Disjoint Degradation Families    |
| - Benchmarks: MAE, RMSE, % Improvement, PICP Coverage, F1-Score   |
+---------------------------------+---------------------------------+
                                  | SQLAlchemy ORM
+---------------------------------v---------------------------------+
|                   Layer 6: Persistence Layer                      |
|       PostgreSQL 16 (Production) / SQLite (Zero-Config Dev)       |
| 12 Relational Entities: profiles, simulations, readings, etc.     |
+-------------------------------------------------------------------+
```

## Architectural Design Principles

### 1. Strict Ground-Truth Segregation (Leakage Prevention)
The `sensor_readings` stream contains only observable telemetry:
- `timestamp`, `simulated_day`, `cumulative_volume_l`, `flow_rate_lpm`, `inlet_tds_ppm`, `outlet_tds_ppm`, `rejection_percentage`, `sensor_status`.

The unobservable internal states (`degradation_index`, `true_rul_days`, `true_rul_litres`, `is_eol`) are stored exclusively in `ground_truth_states`.
Ground truth is **never** fed into feature extraction and is accessible solely by internal evaluation routines.

### 2. Scenario-Level Partitioning
Time-series rows within the same simulation run possess intense autocorrelation. Random row-level splitting causes massive data leakage. FilterTwin splits data strictly at the whole-scenario level. Furthermore, the entire `nonlinear` degradation family is held out from training to validate out-of-distribution generalization.

### 3. Hardware-Ready Common Telemetry Schema
The input schema consumed by the intelligence engine (`flow_rate_lpm`, `inlet_tds_ppm`, `outlet_tds_ppm`, `timestamp`) is identical to the telemetry payload of physical ESP32 flow and dual-probe TDS sensors. Physical sensors can stream directly to `/api/v1/simulations/{id}/readings` without modifying a single line of the predictive engine.
