# FilterTwin: Explainable Filter Diagnostics & Guided Maintenance

> **An uncertainty-aware, simulation-driven predictive maintenance platform for water purifier filters.**

[![License: MIT](https://img.shields.io/badge/License-MIT-teal.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev/)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.4+-f7931e.svg)](https://scikit-learn.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Tests: 24 Passed](https://img.shields.io/badge/tests-24%20passed-brightgreen.svg)]()

---

### Team **CoreCraft**
**Lendi Institute of Engineering and Technology**
- **Harshitha (Team Lead)** – Architecture, Backend Integration & ML Methodology
- **Padmini** – Frontend & Visualization Engine
- **Sowjanya** – Simulation Engine, Testing & Maintenance Workflows

---

## 1. Project Overview & Problem Statement

Conventional water purifier maintenance relies on rigid countdown timers, static volume meters, or arbitrary manufacturer replacement intervals (e.g., replace every 12 months or 5,000 L). These heuristics:
1. **Ignore dynamic water quality**: Inlet TDS fluctuations and sediment loads vary dramatically across geography.
2. **Cannot estimate remaining useful life (RUL)** based on observed hydraulic compaction and membrane salt rejection degradation.
3. **Fail to quantify prediction uncertainty**: Single-point estimates obscure critical decision risks.
4. **Lack explainability**: Users are alerted to replace cartridges without transparent causal factors.
5. **Offer no structured workflow**: After an alert, users lack guided, verified replacement procedures.

**FilterTwin** provides a complete, mathematically grounded, simulation-driven solution utilizing only **100% open-source technologies**. It features a virtual purifier simulator, multiple predictive regression engines, calibrated quantile uncertainty intervals, multi-state anomaly classifiers, an explainability engine, interactive guided maintenance checklists, and a reproducible held-out evaluation benchmark on 200+ scenarios.

---

## 2. High-Level System Architecture

FilterTwin is engineered with a strict 6-layer separation of concerns:

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

---

## 3. Technology Stack (100% Open-Source)

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Frontend** | React 18, Vite | High-performance reactive user interface |
| **Styling** | Tailwind CSS | Modern responsive design system |
| **Visualizations**| Recharts | Interactive time-series & multi-axis telemetry charts |
| **Backend** | Python 3.11, FastAPI | High-throughput asynchronous REST API |
| **Validation** | Pydantic v2 | Strict schema serialization and data validation |
| **Machine Learning**| Scikit-learn, NumPy, Pandas | Ridge Regression, HistGradientBoosting, Quantile Regression |
| **Database** | PostgreSQL 16 (or SQLite) | Relational persistence with SQLAlchemy ORM |
| **Testing** | Pytest, FastAPI TestClient | 24 automated unit, integration, and leakage tests |
| **Deployment** | Docker, Docker Compose | Fully reproducible multi-container orchestration |

*Note: FilterTwin requires zero paid third-party AI APIs. All machine learning inference, uncertainty calibration, and diagnostics execute natively on the open-source backend.*

---

## 4. Empirical Evaluation Benchmark (200 Held-Out Scenarios)

The evaluation suite validates models against **200 unseen scenarios**, including the completely held-out `nonlinear` power degradation family:

### Remaining Useful Life (RUL) Error Comparison
| Model | MAE (days) | RMSE (days) | Improvement vs Baseline (%) | Prediction Interval |
| :--- | :---: | :---: | :---: | :---: |
| **Fixed-Volume Baseline** | 116.03 d | 134.52 d | 0.0% (Benchmark) | N/A |
| **Multivariable Linear Regression** | 41.28 d | 84.49 d | **+64.43%** | 80% Quantile |
| **Gradient Boosted Trees** | 42.03 d | 81.32 d | **+63.77%** | 80% Quantile [Q10 - Q90] |

### Prediction Uncertainty Intervals (Quantile Regression)
- **Empirical Coverage (PICP)**: **66.0%** on unseen out-of-distribution nonlinear curves (91.4% on in-family validation).
- **Average Interval Width**: **48.5 days**.

### Anomaly Detection & Diagnostic Classification
- **Precision**: `0.8944`
- **Recall**: `0.9191` (>90% target achieved!)
- **F1-Score**: `0.9066`
- **False Alert Rate**: `11.16%`
- **Per-Fault Recall Breakdown**:
  - `flow_drop`: **100.0%**
  - `tds_spike`: **100.0%**
  - `sensor_disconnection`: **100.0%**
  - `sensor_drift`: **65.3%**
  - `none` (normal specificity): **88.8%**

---

## 5. Quickstart & Installation

### Option A: Local Development (Quickest)

#### Prerequisites
- Python 3.11+
- Node.js 18+ & npm

#### 1. Backend Setup
```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt

# Run automated model training and held-out evaluation:
python scripts/train_models.py
python scripts/run_evaluation.py

# Start FastAPI server:
uvicorn app.main:app --reload --port 8000
```
Backend will be live at `http://localhost:8000` (Swagger docs at `/docs`).

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

### Option B: Multi-Container Docker Deployment

FilterTwin includes production-ready Dockerfiles and `docker-compose.yml` orchestrating PostgreSQL, FastAPI, and Nginx:

```bash
# Clone the repository
git clone https://github.com/CoreCraft/FilterTwin.git
cd FilterTwin

# Start PostgreSQL, Backend, and Frontend:
docker-compose up --build
```
- Frontend application: `http://localhost:3000`
- Backend API & docs: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432`

---

## 6. Running the Automated Test Suite

Run the complete 24-test suite validating the simulator physics, leakage prevention, feature pipelines, uncertainty bounds, and REST APIs:

```bash
# From workspace root:
$env:PYTHONPATH="backend"
python -m pytest backend/tests/ -v
```

### Verified Test Results (24 Passed):
```
backend/tests/test_simulator.py::test_linear_degradation PASSED
backend/tests/test_simulator.py::test_exponential_degradation PASSED
backend/tests/test_simulator.py::test_nonlinear_degradation PASSED
backend/tests/test_simulator.py::test_abrupt_fault_degradation PASSED
backend/tests/test_simulator.py::test_sensor_bounds_and_drift PASSED
backend/tests/test_simulator.py::test_fault_injection_flow_drop PASSED
backend/tests/test_simulator.py::test_simulator_engine_reproducibility PASSED
backend/tests/test_simulator.py::test_strict_separation_no_data_leakage PASSED
backend/tests/test_features_and_models.py::test_feature_extraction PASSED
backend/tests/test_features_and_models.py::test_fixed_volume_baseline PASSED
backend/tests/test_features_and_models.py::test_linear_regression_model PASSED
backend/tests/test_features_and_models.py::test_gradient_boosting_model PASSED
backend/tests/test_uncertainty_and_anomalies.py::test_quantile_uncertainty_bounds PASSED
backend/tests/test_uncertainty_and_anomalies.py::test_anomaly_detection_normal_state PASSED
backend/tests/test_uncertainty_and_anomalies.py::test_anomaly_detection_flow_drop PASSED
backend/tests/test_uncertainty_and_anomalies.py::test_anomaly_detection_insufficient_data PASSED
backend/tests/test_uncertainty_and_anomalies.py::test_explainability_generation PASSED
backend/tests/test_leakage_and_eval.py::test_no_data_leakage_in_features PASSED
backend/tests/test_leakage_and_eval.py::test_disjoint_scenario_splits PASSED
backend/tests/test_leakage_and_eval.py::test_metric_computations PASSED
backend/tests/test_api_endpoints.py::test_health_endpoint PASSED
backend/tests/test_api_endpoints.py::test_purifier_crud_endpoints PASSED
backend/tests/test_api_endpoints.py::test_simulation_and_diagnostic_flow PASSED
backend/tests/test_api_endpoints.py::test_evaluations_and_maintenance PASSED

======================== 24 passed in 5.13s ========================
```

---

## 7. Interactive Pages in FilterTwin

1. **Dashboard**: High-level purifier health index gauge, estimated RUL, 80% prediction interval, current flow rate, inlet/outlet TDS, and prescriptive action cards. Features prominent `SIMULATED DATA` indicators.
2. **Simulator Studio**: Interactive configuration of degradation laws (Linear, Exponential, Nonlinear, Abrupt), feed water TDS, daily consumption, sensor noise, progressive drift, and controlled fault injection.
3. **Live Monitoring**: Recharts time-series graphs for permeate flow rate, inlet vs product TDS, salt rejection %, and cumulative filtered volume.
4. **Diagnostics & Predictions**: Side-by-side comparison of Baseline vs Linear Regression vs Gradient Boosting RUL, calibrated uncertainty intervals, and standardized factor contribution explanations.
5. **Model Evaluation**: Non-fabricated benchmark on 200+ held-out scenarios with MAE/RMSE comparisons, PICP coverage, confusion matrix, and direct CSV report download.
6. **Maintenance Center**: Step-by-step interactive checklists for RO membranes and sediment pre-filters, safety sign-off, technician notes, and baseline re-establishment.
7. **History & Reports**: Audit logs, past predictions, exportable telemetry CSVs, and complete JSON diagnostic dossiers.

---

## 8. Documentation

- [System Architecture](docs/architecture.md)
- [Mathematical Methodology & Machine Learning](docs/methodology.md)
- [REST API Specification](docs/api_documentation.md)
- [Engineering Limitations & ESP32 Roadmap](docs/limitations.md)

---

## 9. License

This project is licensed under the [MIT License](LICENSE) - free and open for educational and commercial development.
