"""
Feature Engineering for RUL Prediction and Diagnostic Analysis.
Computes multi-signal diagnostic features strictly from observed sensor readings.
Ground truth values are strictly forbidden from entering this pipeline.
"""

import numpy as np
from typing import List, Dict, Any, Optional

FEATURE_NAMES = [
    "cumulative_volume_l",
    "tds_load_g",
    "flow_ratio",
    "rejection_percentage",
    "rejection_trend",
    "daily_consumption_lpd",
    "filter_age_days",
    "rolling_flow_lpm",
]

def extract_features_at_point(
    readings: List[Dict[str, Any]],
    baseline_flow_lpm: float = 2.0,
    nominal_capacity_l: float = 5000.0,
    point_index: Optional[int] = None
) -> Optional[Dict[str, float]]:
    """
    Extracts feature vector at a specific index in reading history (defaulting to latest).
    Readings are processed strictly using information available up to point_index.
    """
    if not readings:
        return None

    if point_index is None:
        idx = len(readings) - 1
    else:
        idx = min(point_index, len(readings) - 1)

    if idx < 0:
        return None

    sub_readings = readings[:idx + 1]
    valid_sub = [
        r for r in sub_readings
        if r.get("flow_rate_lpm") is not None and r.get("flow_rate_lpm", -1) >= 0 and
           r.get("outlet_tds_ppm") is not None and r.get("outlet_tds_ppm", -1) >= 0
    ]

    if not valid_sub:
        return None

    curr = valid_sub[-1]
    first = valid_sub[0]

    # Current telemetry
    curr_flow = float(curr["flow_rate_lpm"])
    curr_inlet = float(curr["inlet_tds_ppm"])
    curr_outlet = float(curr["outlet_tds_ppm"])
    curr_rej = float(curr.get("rejection_percentage") or 0.0)
    curr_vol = float(curr.get("cumulative_volume_l") or 0.0)
    curr_day = float(curr.get("simulated_day") or 0.0)

    # Baseline flow ratio
    b_flow = max(0.1, baseline_flow_lpm)
    flow_ratio = curr_flow / b_flow

    # TDS Load approximation: integral(TDS_in * dV) in grams
    # 1 ppm = 1 mg/L = 0.001 g/L
    tds_load_g = 0.0
    prev_vol = 0.0
    for r in valid_sub:
        vol = float(r.get("cumulative_volume_l") or 0.0)
        d_vol = max(0.0, vol - prev_vol)
        inlet = float(r.get("inlet_tds_ppm") or 500.0)
        tds_load_g += (inlet * d_vol * 0.001)  # mg to g
        prev_vol = vol

    # Rejection trend: difference from early baseline (first 5 readings)
    early_rej = np.mean([float(r.get("rejection_percentage") or 95.0) for r in valid_sub[:min(5, len(valid_sub))]])
    rejection_trend = curr_rej - early_rej

    # Filter age
    filter_age_days = max(1.0, curr_day)

    # Average daily consumption
    daily_consumption_lpd = curr_vol / filter_age_days if filter_age_days > 0 else 15.0

    # Rolling window flow (last 7 readings)
    recent_flows = [float(r["flow_rate_lpm"]) for r in valid_sub[-min(7, len(valid_sub)):]]
    rolling_flow_lpm = float(np.mean(recent_flows))

    return {
        "cumulative_volume_l": float(curr_vol),
        "tds_load_g": float(tds_load_g),
        "flow_ratio": float(flow_ratio),
        "rejection_percentage": float(curr_rej),
        "rejection_trend": float(rejection_trend),
        "daily_consumption_lpd": float(daily_consumption_lpd),
        "filter_age_days": float(filter_age_days),
        "rolling_flow_lpm": float(rolling_flow_lpm),
    }

def features_dict_to_array(f_dict: Dict[str, float]) -> np.ndarray:
    """Converts feature dictionary into standard 2D numpy array for scikit-learn models."""
    row = [f_dict[name] for name in FEATURE_NAMES]
    return np.array([row], dtype=np.float64)
