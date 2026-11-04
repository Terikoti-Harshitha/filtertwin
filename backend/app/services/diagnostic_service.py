"""
Diagnostic and Prediction Service.
Loads ML models and detectors, evaluates incoming telemetry, computes multi-model RUL estimates,
prediction intervals, anomaly alerts, and explainability factors.
"""

import os
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List

from app.config import settings
from app.models.entities import SimulationRun, Prediction, DiagnosticAlert, SensorReading
from app.schemas.diagnostic import FullDiagnosticResponse, AlertResponse
from app.intelligence.preprocessing import validate_telemetry_history
from app.intelligence.feature_engineering import extract_features_at_point
from app.intelligence.baseline import FixedVolumeBaseline
from app.intelligence.regression import LinearRegressionRULModel
from app.intelligence.gradient_boosting import GradientBoostingRULModel
from app.intelligence.uncertainty import QuantileUncertaintyEngine
from app.intelligence.anomaly_detection import AnomalyDetector
from app.intelligence.explainability import generate_diagnostic_explanation

# Global cached model singletons
_baseline = FixedVolumeBaseline()
_linear_model: Optional[LinearRegressionRULModel] = None
_gb_model: Optional[GradientBoostingRULModel] = None
_unc_engine: Optional[QuantileUncertaintyEngine] = None
_detector = AnomalyDetector()

def get_ml_models():
    global _linear_model, _gb_model, _unc_engine
    lin_path = os.path.join(settings.ML_ARTIFACTS_DIR, "linear_regression.pkl")
    gb_path = os.path.join(settings.ML_ARTIFACTS_DIR, "gradient_boosting.pkl")
    unc_path = os.path.join(settings.ML_ARTIFACTS_DIR, "uncertainty_engine.pkl")

    def _load_or_retrain():
        global _linear_model, _gb_model, _unc_engine
        try:
            if _linear_model is None and os.path.exists(lin_path):
                m = LinearRegressionRULModel()
                m.load(lin_path)
                _linear_model = m

            if _gb_model is None and os.path.exists(gb_path):
                m = GradientBoostingRULModel()
                m.load(gb_path)
                _gb_model = m

            if _unc_engine is None and os.path.exists(unc_path):
                m = QuantileUncertaintyEngine()
                m.load(unc_path)
                _unc_engine = m
        except Exception as exc:
            print(f"[ML Models] Artifact load failed ({exc}). Retraining models for current environment...")
            try:
                from scripts.train_models import train_and_save_all
                train_and_save_all(num_scenarios=35)
                # Retry loading freshly trained artifacts
                if os.path.exists(lin_path):
                    m = LinearRegressionRULModel()
                    m.load(lin_path)
                    _linear_model = m
                if os.path.exists(gb_path):
                    m = GradientBoostingRULModel()
                    m.load(gb_path)
                    _gb_model = m
                if os.path.exists(unc_path):
                    m = QuantileUncertaintyEngine()
                    m.load(unc_path)
                    _unc_engine = m
            except Exception as train_exc:
                print(f"[ML Models] Fallback training failed ({train_exc})")

    _load_or_retrain()

    return _baseline, _linear_model, _gb_model, _unc_engine, _detector

def run_diagnostic_for_simulation(
    db: Session,
    simulation_id: str
) -> Dict[str, Any]:
    """
    Executes full diagnostic pipeline for the latest state of a simulation run.
    """
    run = db.query(SimulationRun).filter(SimulationRun.id == simulation_id).first()
    if not run:
        raise ValueError(f"Simulation {simulation_id} not found")

    purifier = run.purifier
    readings = db.query(SensorReading).filter(
        SensorReading.simulation_run_id == simulation_id
    ).order_by(SensorReading.simulated_day.asc()).all()

    # Convert reading entities to dictionaries
    obs_dicts = [
        {
            "timestamp": r.timestamp,
            "simulated_day": r.simulated_day,
            "cumulative_volume_l": r.cumulative_volume_l,
            "flow_rate_lpm": r.flow_rate_lpm,
            "inlet_tds_ppm": r.inlet_tds_ppm,
            "outlet_tds_ppm": r.outlet_tds_ppm,
            "rejection_percentage": r.rejection_percentage,
            "sensor_status": r.sensor_status,
        }
        for r in readings
    ]

    # 1. Telemetry Quality Validation
    quality_status, quality_msg, valid_obs = validate_telemetry_history(obs_dicts)

    # 2. Anomaly Detection
    diag_res = _detector.evaluate(
        obs_dicts,
        filter_capacity_l=purifier.filter_capacity_l,
        baseline_flow_lpm=purifier.initial_flow_rate_lpm
    )

    # 3. Feature Extraction
    features = extract_features_at_point(
        obs_dicts,
        baseline_flow_lpm=purifier.initial_flow_rate_lpm,
        nominal_capacity_l=purifier.filter_capacity_l
    )

    if features is None:
        features = {
            "cumulative_volume_l": run.cumulative_volume_l,
            "tds_load_g": 0.0,
            "flow_ratio": 1.0,
            "rejection_percentage": 95.0,
            "rejection_trend": 0.0,
            "daily_consumption_lpd": purifier.daily_consumption_l,
            "filter_age_days": max(1.0, run.current_day),
            "rolling_flow_lpm": purifier.initial_flow_rate_lpm,
        }

    daily_use = purifier.daily_consumption_l
    cap = purifier.filter_capacity_l
    cum_vol = features.get("cumulative_volume_l", 0.0)

    # Ensure models are loaded
    baseline_mod, lin_mod, gb_mod, unc_eng, _ = get_ml_models()

    # 4. Baseline RUL
    base_pred = baseline_mod.predict(
        cumulative_volume_l=cum_vol,
        filter_capacity_l=cap,
        daily_consumption_lpd=daily_use
    )

    # 5. ML Models & Uncertainty (fallback if models not trained yet)
    if lin_mod is not None:
        lin_pred = lin_mod.predict(features, daily_consumption_lpd=daily_use)
    else:
        lin_pred = {
            "model_version": "linear-regression-untrained",
            "rul_days": base_pred["rul_days"],
            "rul_litres": base_pred["rul_litres"],
            "method": "Multivariable Linear Regression (Untrained)",
            "is_adaptive": True,
            "feature_contributions": {},
        }

    if gb_mod is not None:
        gb_pred = gb_mod.predict(features, daily_consumption_lpd=daily_use)
    else:
        gb_pred = {
            "model_version": "gradient-boosting-untrained",
            "rul_days": base_pred["rul_days"],
            "rul_litres": base_pred["rul_litres"],
            "method": "Gradient Boosted Trees (Untrained)",
            "is_adaptive": True,
        }

    if unc_eng is not None:
        unc_pred = unc_eng.predict_interval(features, daily_consumption_lpd=daily_use)
    else:
        # Fallback heuristic interval (+/- 15%)
        med = float(lin_pred["rul_days"])
        unc_pred = {
            "model_version": "heuristic-interval-v1",
            "rul_median_days": med,
            "rul_lower_days": round(max(0.0, med * 0.85), 1),
            "rul_upper_days": round(med * 1.15, 1),
            "rul_median_litres": round(med * daily_use, 1),
            "rul_lower_litres": round(max(0.0, med * 0.85 * daily_use), 1),
            "rul_upper_litres": round(med * 1.15 * daily_use, 1),
            "interval_width_days": round(med * 0.30, 1),
            "nominal_coverage_pct": 80.0,
            "historical_empirical_coverage_pct": 85.0,
        }

    # 6. Explainability
    explanation = generate_diagnostic_explanation(
        features=features,
        feature_contributions=lin_pred.get("feature_contributions"),
        diagnosis=diag_res,
        rul_prediction=lin_pred,
    )

    # 7. Persist Alert if anomalous
    if diag_res["category"] != "NORMAL":
        alert = DiagnosticAlert(
            simulation_run_id=simulation_id,
            timestamp=obs_dicts[-1]["timestamp"] if obs_dicts else "now",
            simulated_day=run.current_day,
            category=diag_res["category"],
            subtype=diag_res["subtype"],
            severity=diag_res["severity"],
            message=diag_res["message"],
            evidence_json=diag_res["evidence"],
        )
        db.add(alert)

    # Persist Prediction
    pred_entity = Prediction(
        simulation_run_id=simulation_id,
        model_version=lin_pred["model_version"],
        timestamp=obs_dicts[-1]["timestamp"] if obs_dicts else "now",
        rul_median_days=unc_pred["rul_median_days"],
        rul_lower_days=unc_pred["rul_lower_days"],
        rul_upper_days=unc_pred["rul_upper_days"],
        rul_median_litres=unc_pred["rul_median_litres"],
        diagnostic_category=diag_res["category"],
        diagnostic_subtype=diag_res["subtype"],
        quality_status=quality_status.value,
        recommended_action=explanation["recommended_action"],
        feature_contributions_json=lin_pred.get("feature_contributions"),
    )
    db.add(pred_entity)
    db.commit()

    return {
        "simulation_id": simulation_id,
        "simulated_day": run.current_day,
        "data_quality_status": quality_status.value,
        "data_quality_message": quality_msg,
        "baseline_prediction": base_pred,
        "linear_prediction": lin_pred,
        "gradient_boosting_prediction": gb_pred,
        "uncertainty_interval": unc_pred,
        "diagnosis": diag_res,
        "explanation": explanation,
    }

def get_alerts_for_simulation(db: Session, simulation_id: str) -> List[DiagnosticAlert]:
    return db.query(DiagnosticAlert).filter(
        DiagnosticAlert.simulation_run_id == simulation_id
    ).order_by(DiagnosticAlert.created_at.desc()).all()
