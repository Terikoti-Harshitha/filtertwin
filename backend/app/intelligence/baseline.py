"""
Fixed-Volume Baseline Model for Remaining Useful Life (RUL).
Represents traditional industry heuristics using static rated capacity:
RUL_litres = max(0, Capacity - Cumulative_volume)
RUL_days = RUL_litres / Daily_consumption
"""

from typing import Dict, Any

class FixedVolumeBaseline:
    def __init__(self, model_version: str = "fixed-volume-baseline-v1"):
        self.model_version = model_version

    def predict(
        self,
        cumulative_volume_l: float,
        filter_capacity_l: float = 5000.0,
        daily_consumption_lpd: float = 15.0,
    ) -> Dict[str, Any]:
        """
        Computes remaining useful life using the fixed-volume benchmark heuristic.
        """
        capacity = max(100.0, float(filter_capacity_l))
        consumed = max(0.0, float(cumulative_volume_l))
        daily_use = max(0.1, float(daily_consumption_lpd))

        rul_litres = max(0.0, capacity - consumed)
        rul_days = rul_litres / daily_use

        return {
            "model_version": self.model_version,
            "rul_days": round(float(rul_days), 1),
            "rul_litres": round(float(rul_litres), 1),
            "method": "Fixed-Volume Heuristic",
            "is_adaptive": False,
        }
