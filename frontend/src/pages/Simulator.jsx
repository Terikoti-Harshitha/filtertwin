import React, { useState } from 'react';
import {
  Play,
  RotateCcw,
  AlertOctagon,
  Sliders,
  Sparkles,
  Cpu,
  Layers,
  Activity,
  CheckCircle2
} from 'lucide-react';
import { usePurifier } from '../context/PurifierContext';
import api from '../services/api';
import SimulatedDataBadge from '../components/common/SimulatedDataBadge';

export default function Simulator() {
  const { selectedPurifier, activeSimulation, setActiveSimulation, setReadings, refreshDiagnosis } = usePurifier();

  const [degradationType, setDegradationType] = useState('linear');
  const [degradationSpeed, setDegradationSpeed] = useState(1.0);
  const [inletTds, setInletTds] = useState(550);
  const [dailyUse, setDailyUse] = useState(18);
  const [capacity, setCapacity] = useState(5000);
  const [sensorNoise, setSensorNoise] = useState(0.02);
  const [sensorDrift, setSensorDrift] = useState(0.005);
  const [randomSeed, setRandomSeed] = useState(42);
  const [durationDays, setDurationDays] = useState(90);

  // Fault injection state
  const [selectedFault, setSelectedFault] = useState('none');
  const [faultDay, setFaultDay] = useState(30);
  const [faultMagnitude, setFaultMagnitude] = useState(0.5);

  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState(null);

  const handleRunSimulation = async () => {
    if (!selectedPurifier?.id) return;
    setLoading(true);
    setStatusMsg(null);
    try {
      // 1. Update purifier profile with user parameters
      await api.updatePurifier(selectedPurifier.id, {
        initial_inlet_tds: Number(inletTds),
        daily_consumption_l: Number(dailyUse),
        filter_capacity_l: Number(capacity),
        sensor_noise: Number(sensorNoise),
        sensor_drift: Number(sensorDrift),
      });

      // 2. Launch simulation run
      const sim = await api.createSimulation({
        purifier_profile_id: selectedPurifier.id,
        degradation_type: degradationType,
        degradation_speed: Number(degradationSpeed),
        fault_type: selectedFault,
        fault_day: selectedFault !== 'none' ? Number(faultDay) : null,
        fault_magnitude: Number(faultMagnitude),
        random_seed: Number(randomSeed),
        duration_days: Number(durationDays),
      });

      setActiveSimulation(sim);
      const rList = await api.getReadings(sim.id);
      setReadings(rList);
      await refreshDiagnosis();

      setStatusMsg({
        type: 'success',
        text: `Simulation #${sim.id.substring(0, 8)} executed (${rList.length} daily time steps generated).`,
      });
    } catch (err) {
      setStatusMsg({ type: 'error', text: `Failed to run simulation: ${err.message}` });
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    if (!activeSimulation?.id) return;
    try {
      await api.resetSimulation(activeSimulation.id);
      setStatusMsg({ type: 'info', text: 'Simulation state reset to day 0.' });
      handleRunSimulation();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>Virtual Purifier Simulator Studio</span>
            <SimulatedDataBadge />
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Configure physical operating conditions, mathematical degradation profiles, and controlled fault injections.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleReset}
            className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl border border-slate-700 flex items-center gap-1.5 transition"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Scenario</span>
          </button>
          <button
            onClick={handleRunSimulation}
            disabled={loading}
            className="px-4 py-2 bg-teal-500 hover:bg-teal-400 text-slate-950 font-semibold text-xs rounded-xl shadow-lg shadow-teal-500/20 flex items-center gap-1.5 transition disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'Simulating...' : 'Generate Simulation Batch'}</span>
          </button>
        </div>
      </div>

      {statusMsg && (
        <div className={`p-4 rounded-2xl text-xs font-medium border flex items-center gap-2 ${
          statusMsg.type === 'success'
            ? 'bg-emerald-950/30 text-emerald-300 border-emerald-800/40'
            : statusMsg.type === 'error'
            ? 'bg-rose-950/30 text-rose-300 border-rose-800/40'
            : 'bg-slate-900 text-slate-300 border-slate-800'
        }`}>
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{statusMsg.text}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Degradation & Physics */}
        <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-5 lg:col-span-2">
          <div className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-slate-300">
            <Layers className="w-4 h-4 text-teal-400" />
            <span>Degradation Law & Feed Water Parameters</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Degradation Model Selector */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300">Degradation Profile Model</label>
              <select
                value={degradationType}
                onChange={(e) => setDegradationType(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 text-xs rounded-xl p-2.5 text-slate-200 focus:outline-none focus:border-teal-500"
              >
                <option value="linear">Linear Degradation (D = t / T)</option>
                <option value="exponential">Exponential Degradation (e^kt wear curve)</option>
                <option value="nonlinear">Nonlinear Power Curve ((t / T)^p)</option>
                <option value="abrupt">Abrupt Fault Jump (Baseline + Delta)</option>
              </select>
            </div>

            {/* Degradation Speed Multiplier */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-medium">
                <span className="text-slate-300">Wear Acceleration Factor</span>
                <span className="font-mono text-teal-400">{degradationSpeed}x</span>
              </div>
              <input
                type="range"
                min="0.5"
                max="3.0"
                step="0.1"
                value={degradationSpeed}
                onChange={(e) => setDegradationSpeed(e.target.value)}
                className="w-full accent-teal-500"
              />
            </div>

            {/* Inlet TDS */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300">Inlet Feed TDS (ppm)</label>
              <input
                type="number"
                min="50"
                max="2000"
                value={inletTds}
                onChange={(e) => setInletTds(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 text-xs rounded-xl p-2.5 text-slate-200 focus:outline-none focus:border-teal-500 font-mono"
              />
            </div>

            {/* Daily Consumption */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300">Daily Water Consumption (L/day)</label>
              <input
                type="number"
                min="2"
                max="100"
                value={dailyUse}
                onChange={(e) => setDailyUse(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 text-xs rounded-xl p-2.5 text-slate-200 focus:outline-none focus:border-teal-500 font-mono"
              />
            </div>

            {/* Rated Capacity */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300">Nominal Filter Capacity (Litres)</label>
              <input
                type="number"
                min="500"
                max="20000"
                step="500"
                value={capacity}
                onChange={(e) => setCapacity(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 text-xs rounded-xl p-2.5 text-slate-200 focus:outline-none focus:border-teal-500 font-mono"
              />
            </div>

            {/* Simulation Duration */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300">Scenario Duration (Days)</label>
              <input
                type="number"
                min="10"
                max="365"
                value={durationDays}
                onChange={(e) => setDurationDays(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 text-xs rounded-xl p-2.5 text-slate-200 focus:outline-none focus:border-teal-500 font-mono"
              />
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800 grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Sensor Noise */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-medium">
                <span className="text-slate-300">Sensor Noise (Std Dev)</span>
                <span className="font-mono text-teal-400">{(sensorNoise * 100).toFixed(1)}%</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="0.08"
                step="0.005"
                value={sensorNoise}
                onChange={(e) => setSensorNoise(e.target.value)}
                className="w-full accent-teal-500"
              />
            </div>

            {/* Random Seed */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300">PRNG Seed (Deterministic Reproducibility)</label>
              <input
                type="number"
                value={randomSeed}
                onChange={(e) => setRandomSeed(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 text-xs rounded-xl p-2.5 text-slate-200 focus:outline-none focus:border-teal-500 font-mono"
              />
            </div>
          </div>
        </div>

        {/* Right Column: Fault Injection Studio */}
        <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-5">
          <div className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-rose-400">
            <AlertOctagon className="w-4 h-4 text-rose-400" />
            <span>Controlled Fault Injection</span>
          </div>

          <p className="text-xs text-slate-400">
            Introduce acute anomalies into the simulated telemetry stream to test diagnostic classification and robustness.
          </p>

          <div className="space-y-3">
            <label className="text-xs font-medium text-slate-300">Select Fault Scenario</label>
            <div className="space-y-2">
              {[
                { id: 'none', label: 'None (Clean Nominal Wear)', desc: 'Standard stochastic baseline wear.' },
                { id: 'flow_drop', label: 'Sudden Flow Drop', desc: 'Simulates pre-filter clog or valve restriction.' },
                { id: 'tds_spike', label: 'Outlet TDS Spike', desc: 'Simulates membrane rupture or O-ring bypass.' },
                { id: 'sensor_disconnection', label: 'Sensor Disconnection', desc: 'Simulates missing telemetry / telemetry loss.' },
                { id: 'sensor_drift', label: 'Accelerated Sensor Drift', desc: 'Simulates probe fouling / progressive bias.' },
              ].map((f) => (
                <div
                  key={f.id}
                  onClick={() => setSelectedFault(f.id)}
                  className={`p-3 rounded-xl border cursor-pointer transition ${
                    selectedFault === f.id
                      ? 'bg-rose-950/20 border-rose-500/50 text-white'
                      : 'bg-slate-950/50 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <div className="text-xs font-bold">{f.label}</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">{f.desc}</div>
                </div>
              ))}
            </div>

            {selectedFault !== 'none' && (
              <div className="pt-3 border-t border-slate-800 space-y-3">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-300">Fault Injection Day</label>
                  <input
                    type="number"
                    min="1"
                    max={durationDays - 5}
                    value={faultDay}
                    onChange={(e) => setFaultDay(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 text-xs rounded-xl p-2.5 text-slate-200 font-mono"
                  />
                </div>

                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-slate-300">Fault Magnitude</span>
                    <span className="font-mono text-rose-400">{(faultMagnitude * 100).toFixed(0)}%</span>
                  </div>
                  <input
                    type="range"
                    min="0.2"
                    max="0.8"
                    step="0.05"
                    value={faultMagnitude}
                    onChange={(e) => setFaultMagnitude(e.target.value)}
                    className="w-full accent-rose-500"
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
