"""
Data Preprocessing and Telemetry Quality Validation.
Validates incoming sensor observations to detect missing telemetry, disconnected sensors,
and unphysical readings before passing data to ML feature extraction.
"""

from typing import List, Dict, Any, Tuple
from enum import Enum

class QualityStatus(str, Enum):
    GOOD = "GOOD"
    DEGRADED = "DEGRADED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

def validate_telemetry_history(
    readings: List[Dict[str, Any]],
    min_observations: int = 3
) -> Tuple[QualityStatus, str, List[Dict[str, Any]]]:
    """
    Validates observation history for a virtual purifier.
    Returns (quality_status, reason_message, clean_valid_readings).
    """
    if not readings or len(readings) < min_observations:
        return (
            QualityStatus.INSUFFICIENT_DATA,
            f"Insufficient history: {len(readings) if readings else 0} observations available (minimum {min_observations} required).",
            []
        )

    valid_readings = []
    missing_count = 0

    for r in readings:
        flow = r.get("flow_rate_lpm")
        inlet_tds = r.get("inlet_tds_ppm")
        outlet_tds = r.get("outlet_tds_ppm")
        sensor_status = r.get("sensor_status", "normal")

        # Disconnection sentinel or None
        if (
            flow is None or flow < 0 or
            inlet_tds is None or inlet_tds < 0 or
            outlet_tds is None or outlet_tds < 0 or
            sensor_status == "insufficient_data"
        ):
            missing_count += 1
            continue

        valid_readings.append(r)

    total = len(readings)
    missing_ratio = missing_count / total if total > 0 else 1.0

    # If the latest reading is disconnected, immediately flag insufficient data
    latest = readings[-1]
    if (
        latest.get("flow_rate_lpm") is None or latest.get("flow_rate_lpm", -1) < 0 or
        latest.get("outlet_tds_ppm") is None or latest.get("outlet_tds_ppm", -1) < 0
    ):
        return (
            QualityStatus.INSUFFICIENT_DATA,
            "Active sensor disconnection detected on latest observation.",
            valid_readings
        )

    if missing_ratio > 0.40 or len(valid_readings) < min_observations:
        return (
            QualityStatus.INSUFFICIENT_DATA,
            f"Telemetry data quality is severely compromised ({int(missing_ratio * 100)}% missing observations).",
            valid_readings
        )

    if missing_ratio > 0.10:
        return (
            QualityStatus.DEGRADED,
            f"Noticeable telemetry dropouts observed ({int(missing_ratio * 100)}% missing), predictions may have wider uncertainty.",
            valid_readings
        )

    return (QualityStatus.GOOD, "Telemetry data quality is healthy.", valid_readings)
