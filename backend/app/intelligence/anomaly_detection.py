"""
Anomaly Detection and Diagnostic Classification Engine.
Implements:
1. Data Quality Gate (INSUFFICIENT_DATA)
2. Abrupt Anomaly Detection (CUSUM & Rolling Z-Scores for flow drops & TDS spikes)
3. Gradual Wear Classification (Trend slopes, flow ratio depletion, volume exhaustion)
4. Normal State (Healthy operating conditions)
"""

import numpy as np
from enum import Enum
from typing import List, Dict, Any, Tuple, Optional

class DiagnosticCategory(str, Enum):
    NORMAL = "NORMAL"
    GRADUAL_WEAR = "GRADUAL_WEAR"
    ABRUPT_ANOMALY = "ABRUPT_ANOMALY"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

class AnomalySubtype(str, Enum):
    NONE = "none"
    FLOW_DROP = "flow_drop"
    TDS_SPIKE = "tds_spike"
    SENSOR_DISCONNECTION = "sensor_disconnection"
    SENSOR_DRIFT = "sensor_drift"
    PROGRESSIVE_CLOGGING = "progressive_clogging"
    CAPACITY_EXHAUSTION = "capacity_exhaustion"

class AnomalyDetector:
    def __init__(
        self,
        z_threshold: float = 3.0,
        flow_drop_ratio_threshold: float = 0.35, # Sudden 35% drop
        tds_spike_ratio_threshold: float = 0.40, # Sudden 40% rise
        gradual_flow_threshold: float = 0.70,     # Flow ratio under 70% of baseline
        gradual_rejection_drop: float = -12.0,   # Rejection dropped >12% from early baseline
        gradual_volume_ratio: float = 0.85,      # Over 85% of rated capacity
    ):
        self.z_threshold = z_threshold
        self.flow_drop_ratio_threshold = flow_drop_ratio_threshold
        self.tds_spike_ratio_threshold = tds_spike_ratio_threshold
        self.gradual_flow_threshold = gradual_flow_threshold
        self.gradual_rejection_drop = gradual_rejection_drop
        self.gradual_volume_ratio = gradual_volume_ratio

    def evaluate(
        self,
        readings: List[Dict[str, Any]],
        filter_capacity_l: float = 5000.0,
        baseline_flow_lpm: float = 2.0,
    ) -> Dict[str, Any]:
        """
        Evaluates the reading sequence and classifies operating condition.
        Returns diagnostic dictionary with category, subtype, confidence, severity, and evidence.
        """
        # 1. Gate: Check for insufficient data or disconnected sensors
        if not readings or len(readings) < 3:
            return {
                "category": DiagnosticCategory.INSUFFICIENT_DATA.value,
                "subtype": AnomalySubtype.SENSOR_DISCONNECTION.value,
                "confidence": 1.0,
                "severity": "CRITICAL",
                "message": "Telemetry stream contains insufficient observations to form a reliable diagnosis.",
                "evidence": ["Fewer than 3 valid historical readings available."],
                "suppress_rul": True,
            }

        latest = readings[-1]
        flow = latest.get("flow_rate_lpm")
        inlet_tds = latest.get("inlet_tds_ppm")
        outlet_tds = latest.get("outlet_tds_ppm")

        if flow is None or flow < 0 or outlet_tds is None or outlet_tds < 0:
            return {
                "category": DiagnosticCategory.INSUFFICIENT_DATA.value,
                "subtype": AnomalySubtype.SENSOR_DISCONNECTION.value,
                "confidence": 1.0,
                "severity": "CRITICAL",
                "message": "Active sensor disconnection or missing telemetry detected.",
                "evidence": ["Missing or negative readings on current time step."],
                "suppress_rul": True,
            }

        # Filter out invalid readings for statistical rolling window
        valid_readings = [
            r for r in readings
            if r.get("flow_rate_lpm") is not None and r.get("flow_rate_lpm", -1) >= 0 and
               r.get("outlet_tds_ppm") is not None and r.get("outlet_tds_ppm", -1) >= 0
        ]

        if len(valid_readings) < 3:
            return {
                "category": DiagnosticCategory.INSUFFICIENT_DATA.value,
                "subtype": AnomalySubtype.SENSOR_DISCONNECTION.value,
                "confidence": 0.95,
                "severity": "HIGH",
                "message": "Too many missing readings to compute rolling statistics.",
                "evidence": ["Valid telemetry points below minimum required."],
                "suppress_rul": True,
            }

        # 2. Check for Abrupt Anomalies (Sudden flow drop or TDS spike)
        curr_flow = float(latest["flow_rate_lpm"])
        curr_outlet = float(latest["outlet_tds_ppm"])
        curr_inlet = float(latest.get("inlet_tds_ppm") or 500.0)
        curr_vol = float(latest.get("cumulative_volume_l") or 0.0)
        curr_rej = float(latest.get("rejection_percentage") or 0.0)

        # Baseline window from previous readings (excluding current reading)
        history = valid_readings[:-1]
        if len(history) >= 2:
            prev_window = history[-min(10, len(history)):]
            avg_prev_flow = float(np.mean([r["flow_rate_lpm"] for r in prev_window]))
            avg_prev_outlet = float(np.mean([r["outlet_tds_ppm"] for r in prev_window]))
            std_prev_flow = max(0.01, float(np.std([r["flow_rate_lpm"] for r in prev_window])))
            std_prev_outlet = max(0.01, float(np.std([r["outlet_tds_ppm"] for r in prev_window])))

            # Z-scores
            z_flow = (curr_flow - avg_prev_flow) / std_prev_flow
            z_tds = (curr_outlet - avg_prev_outlet) / std_prev_outlet

            # Relative jump
            flow_drop_ratio = (avg_prev_flow - curr_flow) / avg_prev_flow if avg_prev_flow > 0 else 0.0
            tds_rise_ratio = (curr_outlet - avg_prev_outlet) / curr_inlet if curr_inlet > 0 else 0.0

            if flow_drop_ratio > self.flow_drop_ratio_threshold or z_flow < -self.z_threshold:
                return {
                    "category": DiagnosticCategory.ABRUPT_ANOMALY.value,
                    "subtype": AnomalySubtype.FLOW_DROP.value,
                    "confidence": round(min(0.99, 0.70 + abs(z_flow) * 0.05), 2),
                    "severity": "HIGH",
                    "message": "Sudden hydraulic restriction or acute flow drop detected.",
                    "evidence": [
                        f"Current flow {curr_flow:.2f} LPM is {int(flow_drop_ratio * 100)}% below recent average ({avg_prev_flow:.2f} LPM).",
                        f"Flow statistical Z-score: {z_flow:.2f}."
                    ],
                    "suppress_rul": False,
                }

            if tds_rise_ratio > self.tds_spike_ratio_threshold or z_tds > self.z_threshold:
                return {
                    "category": DiagnosticCategory.ABRUPT_ANOMALY.value,
                    "subtype": AnomalySubtype.TDS_SPIKE.value,
                    "confidence": round(min(0.99, 0.70 + z_tds * 0.05), 2),
                    "severity": "HIGH",
                    "message": "Sudden outlet TDS spike detected, indicating possible membrane breach or seal bypass.",
                    "evidence": [
                        f"Outlet TDS jumped to {curr_outlet:.1f} ppm (prior average: {avg_prev_outlet:.1f} ppm).",
                        f"TDS statistical Z-score: {z_tds:.2f}."
                    ],
                    "suppress_rul": False,
                }

        # 3. Check for Gradual Wear
        b_flow = max(0.1, baseline_flow_lpm)
        flow_ratio = curr_flow / b_flow
        vol_ratio = curr_vol / max(100.0, filter_capacity_l)

        early_rej = np.mean([float(r.get("rejection_percentage") or 95.0) for r in valid_sub_slice(valid_readings, 5)])
        rej_diff = curr_rej - early_rej

        # Sensor drift detection: outlet TDS steadily climbing without flow drop
        if len(valid_readings) >= 15:
            # Check slope of outlet TDS over last 15 points
            tds_vals = [r["outlet_tds_ppm"] for r in valid_readings[-15:]]
            days = [r["simulated_day"] for r in valid_readings[-15:]]
            if len(set(days)) > 1:
                slope = np.polyfit(days, tds_vals, 1)[0]
                if slope > 0.8 and flow_ratio > 0.85 and vol_ratio < 0.6:
                    return {
                        "category": DiagnosticCategory.GRADUAL_WEAR.value,
                        "subtype": AnomalySubtype.SENSOR_DRIFT.value,
                        "confidence": 0.82,
                        "severity": "MEDIUM",
                        "message": "Progressive sensor calibration drift detected.",
                        "evidence": [
                            f"Outlet TDS is climbing at {slope:.2f} ppm/day while flow remains unconstrained.",
                            "Sensor quality warning: calibrate or inspect probe."
                        ],
                        "suppress_rul": False,
                    }

        # Progressive clogging / gradual wear
        if flow_ratio < self.gradual_flow_threshold or rej_diff < self.gradual_rejection_drop or vol_ratio > self.gradual_volume_ratio:
            evidence = []
            if flow_ratio < self.gradual_flow_threshold:
                evidence.append(f"Flow ratio has declined to {int(flow_ratio * 100)}% of initial baseline ({b_flow:.2f} LPM).")
            if rej_diff < self.gradual_rejection_drop:
                evidence.append(f"TDS rejection decreased by {abs(rej_diff):.1f}% from initial baseline.")
            if vol_ratio > self.gradual_volume_ratio:
                evidence.append(f"Cumulative filtered volume has reached {int(vol_ratio * 100)}% of rated capacity.")

            subtype = AnomalySubtype.CAPACITY_EXHAUSTION.value if vol_ratio > self.gradual_volume_ratio else AnomalySubtype.PROGRESSIVE_CLOGGING.value

            return {
                "category": DiagnosticCategory.GRADUAL_WEAR.value,
                "subtype": subtype,
                "confidence": 0.88,
                "severity": "MEDIUM",
                "message": "Progressive filter wear and performance degradation observed.",
                "evidence": evidence,
                "suppress_rul": False,
            }

        # 4. Clean Normal State
        return {
            "category": DiagnosticCategory.NORMAL.value,
            "subtype": AnomalySubtype.NONE.value,
            "confidence": 0.95,
            "severity": "LOW",
            "message": "Operating parameters are within normal nominal boundaries.",
            "evidence": [
                f"Flow ratio is {int(flow_ratio * 100)}% of baseline.",
                f"TDS rejection is stable at {curr_rej:.1f}%.",
                f"Cumulative volume is at {int(vol_ratio * 100)}% of capacity."
            ],
            "suppress_rul": False,
        }

def valid_sub_slice(readings: List[Dict[str, Any]], count: int) -> List[Dict[str, Any]]:
    return readings[:min(count, len(readings))]
