"""
Degradation Models for FilterTwin Virtual Purifier.
Implements mathematically grounded degradation profiles:
1. Linear Degradation: D(t) = min(1.0, t / T)
2. Exponential Degradation: D(t) = min(1.0, (exp(k*t) - 1) / (exp(k*T) - 1))
3. Nonlinear Degradation: D(t) = min(1.0, (t / T)^p)
4. Abrupt Degradation: Sudden step change at fault injection time t_f
"""

import numpy as np
from enum import Enum
from typing import Optional

class DegradationType(str, Enum):
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    NONLINEAR = "nonlinear"
    ABRUPT = "abrupt"

class DegradationModel:
    def __init__(
        self,
        model_type: DegradationType = DegradationType.LINEAR,
        nominal_lifetime_days: float = 365.0,
        rate_k: float = 0.015,
        power_p: float = 1.8,
        abrupt_time: Optional[float] = None,
        abrupt_delta: float = 0.45,
    ):
        self.model_type = model_type
        self.T = max(1.0, float(nominal_lifetime_days))
        self.k = float(rate_k)
        self.p = float(power_p)
        self.abrupt_time = abrupt_time
        self.abrupt_delta = float(abrupt_delta)

    def compute(self, t: float) -> float:
        """
        Compute hidden degradation index D(t) in [0.0, 1.0].
        D = 0.0: Brand new filter.
        D = 1.0: End-of-life condition reached.
        """
        if t <= 0:
            return 0.0

        if self.model_type == DegradationType.LINEAR:
            d = t / self.T

        elif self.model_type == DegradationType.EXPONENTIAL:
            denom = np.exp(self.k * self.T) - 1.0
            if abs(denom) < 1e-8:
                d = t / self.T
            else:
                d = (np.exp(self.k * t) - 1.0) / denom

        elif self.model_type == DegradationType.NONLINEAR:
            d = (t / self.T) ** self.p

        elif self.model_type == DegradationType.ABRUPT:
            # Baseline is linear until abrupt time
            d_base = t / self.T
            if self.abrupt_time is not None and t >= self.abrupt_time:
                d = d_base + self.abrupt_delta
            else:
                d = d_base
        else:
            d = t / self.T

        return float(np.clip(d, 0.0, 1.0))

    def solve_eol_time(self) -> float:
        """
        Determine the exact simulated time T_EOL at which D(t) reaches 1.0.
        """
        if self.model_type == DegradationType.LINEAR:
            return self.T

        elif self.model_type == DegradationType.EXPONENTIAL:
            return self.T

        elif self.model_type == DegradationType.NONLINEAR:
            return self.T

        elif self.model_type == DegradationType.ABRUPT:
            if self.abrupt_time is None:
                return self.T
            # Before abrupt time: reaches 1.0 at T
            # If abrupt occurs at t_f, d jump = (t_f/T) + delta.
            # If (t_f/T) + delta >= 1.0, eol is t_f.
            if (self.abrupt_time / self.T) + self.abrupt_delta >= 1.0:
                return self.abrupt_time
            # After t_f: (t/T) + delta = 1.0 => t = (1 - delta) * T
            return max(self.abrupt_time, (1.0 - self.abrupt_delta) * self.T)

        return self.T
