"""
Sensor Models for Virtual Water Purifier.
Models hydraulic flow, TDS transport, membrane rejection, sensor noise and progressive drift.
"""

import numpy as np
from typing import Tuple

class SensorModel:
    def __init__(
        self,
        initial_flow_rate_lpm: float = 2.0,
        flow_alpha: float = 0.50,
        initial_rejection_ratio: float = 0.95,
        rejection_beta: float = 0.30,
        noise_level: float = 0.02, # 2% relative standard deviation
        drift_rate: float = 0.005,  # 0.5% progressive bias per 100 days
        rng: np.random.Generator = None,
    ):
        self.q0 = float(initial_flow_rate_lpm)
        self.alpha = float(flow_alpha)
        self.r0 = float(initial_rejection_ratio)
        self.beta = float(rejection_beta)
        self.noise_level = float(noise_level)
        self.drift_rate = float(drift_rate)
        self.rng = rng if rng is not None else np.random.default_rng(42)

    def generate_flow_rate(
        self,
        degradation: float,
        simulated_day: float,
        apply_drift: bool = True
    ) -> Tuple[float, float]:
        """
        Calculates observed flow rate (L/min) and noise component.
        Q(t) = Q_0 * (1 - alpha * D(t)) + drift + epsilon
        """
        true_q = self.q0 * max(0.05, 1.0 - self.alpha * degradation)
        
        # Progressive drift
        drift = (self.drift_rate * (simulated_day / 100.0) * self.q0) if apply_drift else 0.0
        
        # Measurement noise
        sigma = self.noise_level * self.q0
        noise = self.rng.normal(0.0, sigma) if sigma > 0 else 0.0
        
        observed_q = max(0.0, true_q + drift + noise)
        return float(observed_q), float(noise)

    def generate_tds_readings(
        self,
        inlet_tds_ppm: float,
        degradation: float,
        simulated_day: float,
        apply_drift: bool = True
    ) -> Tuple[float, float, float]:
        """
        Calculates observed outlet TDS (ppm), rejection ratio, and rejection percentage.
        R(t) = clamp(R_0 - beta * D(t), 0.0, 1.0)
        TDS_out(t) = TDS_in * (1 - R(t)) + drift + epsilon
        """
        # True simulated rejection ratio
        true_r = np.clip(self.r0 - self.beta * degradation, 0.0, 0.999)
        
        # True outlet TDS
        true_tds_out = inlet_tds_ppm * (1.0 - true_r)
        
        # Progressive drift (e.g. sensor fouling causing upward drift in reported TDS)
        drift = (self.drift_rate * (simulated_day / 100.0) * inlet_tds_ppm) if apply_drift else 0.0
        
        # Measurement noise
        sigma = self.noise_level * max(10.0, true_tds_out)
        noise = self.rng.normal(0.0, sigma) if sigma > 0 else 0.0
        
        observed_tds_out = max(0.0, min(inlet_tds_ppm, true_tds_out + drift + noise))
        
        # Computed rejection % from observed readings
        if inlet_tds_ppm > 0:
            rejection_pct = ((inlet_tds_ppm - observed_tds_out) / inlet_tds_ppm) * 100.0
        else:
            rejection_pct = 0.0

        return float(observed_tds_out), float(true_r), float(np.clip(rejection_pct, 0.0, 100.0))
