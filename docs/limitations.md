# FilterTwin Engineering Limitations & Future Scope

## 1. Documented Scope & Simulation Assumptions
FilterTwin v1.0 is an intentionally **software-only, simulation-driven platform**. It establishes algorithmic predictive maintenance and explainable diagnostics using mathematical models. It does not claim real-world physical sensor validation or drinking water potability certification.

### Specific Technical Limitations:
1. **Mathematical Approximation vs. Physical Cartridge Physics**:
   Real membrane compaction, biological biofilm formation, and colloidal fouling are highly complex, multi-physics phenomena. The simulated linear, exponential, and nonlinear wear models provide controlled testing environments for ML algorithms, but do not replace certified physical laboratory endurance trials.
2. **TDS as a Surrogate Metric**:
   Total Dissolved Solids (TDS) measures electrical conductivity of dissolved ionic minerals. It does not measure microbiological pathogens (bacteria, viruses), microplastics, heavy metals, pesticides, or VOCs. Low outlet TDS cannot establish microbiological water safety.
3. **Hydraulic Variability**:
   Hydraulic flow drops can occur due to fluctuations in municipal feed line pressure, booster pump wear, or kinked polyethylene tubing, rather than solely cartridge media compaction.
4. **Maintenance Verification**:
   The interactive checklist validates human operator procedure completion and re-establishes analytical baselines. It cannot physically verify that a genuine cartridge was properly seated or that O-rings were lubricated.

---

## 2. Future Hardware Integration Roadmap (ESP32)

FilterTwin's telemetry schema (`flow_rate_lpm`, `inlet_tds_ppm`, `outlet_tds_ppm`, `timestamp`) was deliberately designed to match standard IoT hardware payloads.

In future releases:
- **Physical Sensor Interfacing**: Dual analog TDS probes and Hall-effect flow turbine meters connected to an ESP32 micro-controller.
- **MQTT / WebSocket Telemetry Ingestion**: Streaming real-time packet ingestion directly into `/api/v1/simulations/{id}/readings`.
- **Empirical Field Datasets**: Model retraining on physical accelerated cartridge degradation data.
- **Microbiological Indicator Support**: Integration of optical turbidity and UV-C sensors.
