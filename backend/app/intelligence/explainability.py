"""
Explainability Engine for Filter Diagnostics.
Translates statistical model weights, sensor residual shifts, and feature contributions
into transparent, human-interpretable diagnostic factors and maintenance recommendations.
"""

from typing import List, Dict, Any, Optional

def generate_diagnostic_explanation(
    features: Dict[str, float],
    feature_contributions: Optional[Dict[str, float]],
    diagnosis: Dict[str, Any],
    rul_prediction: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Synthesizes model observations, contributions, and diagnostic evidence into a coherent explanation.
    """
    category = diagnosis.get("category", "NORMAL")
    subtype = diagnosis.get("subtype", "none")
    evidence = diagnosis.get("evidence", [])
    
    factors: List[Dict[str, Any]] = []

    # 1. Flow Ratio
    flow_ratio = features.get("flow_ratio", 1.0)
    flow_contrib = feature_contributions.get("flow_ratio", 0.0) if feature_contributions else 0.0
    if flow_ratio < 0.70:
        factors.append({
            "factor": "Flow Ratio",
            "observed_value": f"{flow_ratio * 100:.1f}% of baseline",
            "direction": "negative",
            "impact_magnitude": abs(flow_contrib),
            "description": "Flow rate has declined noticeably from baseline, indicating possible physical sediment restriction or media compaction."
        })
    elif flow_ratio < 0.85:
        factors.append({
            "factor": "Flow Ratio",
            "observed_value": f"{flow_ratio * 100:.1f}% of baseline",
            "direction": "mild_negative",
            "impact_magnitude": abs(flow_contrib),
            "description": "Flow rate shows mild progressive decline."
        })
    else:
        factors.append({
            "factor": "Flow Ratio",
            "observed_value": f"{flow_ratio * 100:.1f}% of baseline",
            "direction": "neutral",
            "impact_magnitude": abs(flow_contrib),
            "description": "Flow rate remains in the optimal operating range."
        })

    # 2. TDS Exposure / Cumulative Load
    tds_load = features.get("tds_load_g", 0.0)
    tds_contrib = feature_contributions.get("tds_load_g", 0.0) if feature_contributions else 0.0
    if tds_load > 2000.0:
        factors.append({
            "factor": "TDS Solid Load",
            "observed_value": f"{tds_load:.0f} g cumulative solids",
            "direction": "negative",
            "impact_magnitude": abs(tds_contrib),
            "description": "High cumulative dissolved solids processed by the membrane, accelerating boundary layer concentration."
        })
    else:
        factors.append({
            "factor": "TDS Solid Load",
            "observed_value": f"{tds_load:.0f} g cumulative solids",
            "direction": "neutral",
            "impact_magnitude": abs(tds_contrib),
            "description": "Accumulated incoming dissolved solids remain within expected design parameters."
        })

    # 3. Rejection Trend
    rej_trend = features.get("rejection_trend", 0.0)
    curr_rej = features.get("rejection_percentage", 95.0)
    rej_contrib = feature_contributions.get("rejection_trend", 0.0) if feature_contributions else 0.0
    if rej_trend < -10.0:
        factors.append({
            "factor": "Rejection Trend",
            "observed_value": f"{curr_rej:.1f}% ({rej_trend:+.1f}% shift)",
            "direction": "negative",
            "impact_magnitude": abs(rej_contrib),
            "description": "Significant degradation in salt rejection efficiency, signaling potential membrane pore wear or fouling."
        })
    else:
        factors.append({
            "factor": "Rejection Trend",
            "observed_value": f"{curr_rej:.1f}% ({rej_trend:+.1f}% shift)",
            "direction": "neutral",
            "impact_magnitude": abs(rej_contrib),
            "description": "Membrane salt rejection remains within stable bounds."
        })

    # 4. Volumetric Utilization
    cum_vol = features.get("cumulative_volume_l", 0.0)
    factors.append({
        "factor": "Cumulative Volume",
        "observed_value": f"{cum_vol:.0f} Litres",
        "direction": "neutral" if cum_vol < 4000 else "negative",
        "impact_magnitude": abs(feature_contributions.get("cumulative_volume_l", 0.0)) if feature_contributions else 0.0,
        "description": f"Total simulated water filtered to date is {cum_vol:.0f} L."
    })

    # Sort factors by impact magnitude if available
    factors.sort(key=lambda x: x["impact_magnitude"], reverse=True)

    # Determine recommended action
    if category == "INSUFFICIENT_DATA":
        recommended_action = "CHECK_SENSOR_CONNECTIONS"
        action_summary = "Verify physical sensor wiring and telemetry connection. RUL prediction is suppressed until valid data stream is re-established."
    elif category == "ABRUPT_ANOMALY":
        if subtype == "FLOW_DROP":
            recommended_action = "INSPECT_PRE_FILTER_HYDRAULICS"
            action_summary = "Check pre-filter cartridges for acute blockage, kinked tubing, or inlet valve shutoff."
        elif subtype == "TDS_SPIKE":
            recommended_action = "TEST_MEMBRANE_INTEGRITY"
            action_summary = "Immediate inspection recommended: test for membrane housing seal bypass or internal element rupture."
        else:
            recommended_action = "INSPECT_SYSTEM"
            action_summary = "Investigate sudden anomaly event."
    elif category == "GRADUAL_WEAR":
        rul_days = rul_prediction.get("rul_days", 30) if rul_prediction else 30
        if rul_days < 15:
            recommended_action = "ORDER_REPLACEMENT_CARTRIDGE"
            action_summary = f"Filter has reached final operational wear phase (estimated {rul_days:.0f} days remaining). Schedule cartridge replacement."
        else:
            recommended_action = "ROUTINE_MONITORING"
            action_summary = f"Progressive wear observed. Filter functioning with {rul_days:.0f} estimated days remaining."
    else:
        recommended_action = "CONTINUE_NORMAL_OPERATION"
        action_summary = "System is operating normally within expected efficiency thresholds. No maintenance required."

    return {
        "diagnostic_category": category,
        "diagnostic_subtype": subtype,
        "contributing_factors": factors,
        "observed_evidence": evidence,
        "recommended_action": recommended_action,
        "action_summary": action_summary,
        "disclaimer": "Diagnostic explanations are based on statistical simulation models and telemetry correlations. Always follow manufacturer-approved maintenance protocols."
    }
