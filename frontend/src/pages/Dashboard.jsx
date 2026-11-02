import React from 'react';
import {
  Droplets,
  Gauge,
  Calendar,
  AlertTriangle,
  ArrowRight,
  TrendingDown,
  ShieldCheck,
  Activity,
  Zap
} from 'lucide-react';
import { usePurifier } from '../context/PurifierContext';
import MetricCard from '../components/common/MetricCard';
import StatusIndicator from '../components/common/StatusIndicator';
import SimulatedDataBadge from '../components/common/SimulatedDataBadge';

export default function Dashboard({ setActiveTab }) {
  const { selectedPurifier, activeSimulation, readings, latestDiagnosis, alerts } = usePurifier();

  const latestReading = readings.length > 0 ? readings[readings.length - 1] : null;

  // Calculate simulated health percentage: (1.0 - cumulative_volume / capacity) or from rejection
  const capacity = selectedPurifier?.filter_capacity_l || 5000.0;
  const consumed = latestReading?.cumulative_volume_l || 0.0;
  const healthPct = Math.max(0, Math.min(100, Math.round(((capacity - consumed) / capacity) * 100)));

  const rulMedianDays = latestDiagnosis?.uncertainty_interval?.rul_median_days ?? '--';
  const rulLowerDays = latestDiagnosis?.uncertainty_interval?.rul_lower_days ?? '--';
  const rulUpperDays = latestDiagnosis?.uncertainty_interval?.rul_upper_days ?? '--';
  const empiricalCoverage = latestDiagnosis?.uncertainty_interval?.historical_empirical_coverage_pct ?? 85;

  const currentFlow = latestReading?.flow_rate_lpm != null ? `${latestReading.flow_rate_lpm} LPM` : '--';
  const currentInlet = latestReading?.inlet_tds_ppm != null ? `${latestReading.inlet_tds_ppm} ppm` : '--';
  const currentOutlet = latestReading?.outlet_tds_ppm != null ? `${latestReading.outlet_tds_ppm} ppm` : '--';
  const currentRej = latestReading?.rejection_percentage != null ? `${latestReading.rejection_percentage}%` : '--';

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-slate-900 via-slate-900 to-teal-950/40 border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-xl font-bold tracking-tight text-white">{selectedPurifier?.name || 'Virtual RO Purifier'}</h1>
            <SimulatedDataBadge />
          </div>
          <p className="text-xs text-slate-400">
            Monitoring profile: <span className="text-slate-300 font-medium">{selectedPurifier?.location}</span> • Rated capacity: <span className="text-slate-300 font-medium">{capacity.toLocaleString()} L</span>
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('simulator')}
            className="px-4 py-2 bg-teal-500 hover:bg-teal-400 text-slate-950 font-semibold text-xs rounded-xl shadow-lg shadow-teal-500/20 transition flex items-center gap-1.5"
          >
            <Zap className="w-3.5 h-3.5" />
            <span>Launch Simulation Studio</span>
          </button>
          <button
            onClick={() => setActiveTab('diagnostics')}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition flex items-center gap-1.5"
          >
            <span>Full Diagnostics</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main KPI Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Health Index Card */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center gap-4">
          <div className="relative w-16 h-16 flex items-center justify-center">
            <svg className="w-16 h-16 transform -rotate-90">
              <circle cx="32" cy="32" r="26" stroke="#1e293b" strokeWidth="6" fill="transparent" />
              <circle
                cx="32"
                cy="32"
                r="26"
                stroke={healthPct > 50 ? '#14b8a6' : healthPct > 25 ? '#f59e0b' : '#f43f5e'}
                strokeWidth="6"
                strokeDasharray={163}
                strokeDashoffset={163 - (163 * healthPct) / 100}
                strokeLinecap="round"
                fill="transparent"
                className="transition-all duration-700 ease-out"
              />
            </svg>
            <span className="absolute font-mono font-bold text-sm text-white">{healthPct}%</span>
          </div>
          <div>
            <span className="text-xs text-slate-400 uppercase font-medium">Filter Health Index</span>
            <div className="text-base font-bold text-white mt-0.5">
              {healthPct > 60 ? 'Optimal Condition' : healthPct > 30 ? 'Moderate Wear' : 'Critical Wear'}
            </div>
            <p className="text-[11px] text-slate-500 mt-1">Based on simulated hydraulic wear</p>
          </div>
        </div>

        {/* Remaining Useful Life Card */}
        <div className="p-5 rounded-2xl bg-teal-950/20 border border-teal-800/40 relative overflow-hidden">
          <div className="flex items-center justify-between text-xs text-teal-400 font-medium uppercase tracking-wider mb-2">
            <span>Remaining Useful Life</span>
            <Calendar className="w-4 h-4 text-teal-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-extrabold font-mono text-teal-300">{rulMedianDays}</span>
            <span className="text-xs text-teal-400/80 font-medium">estimated days</span>
          </div>
          <div className="mt-2 text-[11px] text-teal-200/70 font-mono flex items-center gap-1.5">
            <span>80% Interval:</span>
            <span className="font-semibold text-teal-100">[{rulLowerDays} – {rulUpperDays}] days</span>
          </div>
        </div>

        {/* Diagnostic Status Card */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium uppercase tracking-wider mb-2">
            <span>Diagnostic State</span>
            <Activity className="w-4 h-4 text-slate-400" />
          </div>
          <div className="mt-1">
            <StatusIndicator category={latestDiagnosis?.diagnosis?.category || 'NORMAL'} size="lg" />
          </div>
          <p className="mt-2 text-[11px] text-slate-400 line-clamp-1">
            {latestDiagnosis?.diagnosis?.message || 'Readings are within expected bounds.'}
          </p>
        </div>

        {/* Volume Processed */}
        <MetricCard
          title="Cumulative Water Filtered"
          value={consumed.toLocaleString()}
          unit="Litres"
          subtext={`${((consumed / capacity) * 100).toFixed(1)}% of ${capacity.toLocaleString()} L rated capacity`}
          icon={Droplets}
        />
      </div>

      {/* Telemetry Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="Permeate Flow Rate"
          value={currentFlow}
          unit=""
          subtext={`Baseline nominal: ${selectedPurifier?.initial_flow_rate_lpm || 2.0} LPM`}
          icon={Gauge}
        />
        <MetricCard
          title="Raw Feed Water TDS"
          value={currentInlet}
          unit=""
          subtext="Inlet mineral dissolved solids"
          icon={Droplets}
        />
        <MetricCard
          title="Purified Product TDS"
          value={currentOutlet}
          unit=""
          subtext="Post-membrane dissolved solids"
          icon={Droplets}
        />
        <MetricCard
          title="TDS Salt Rejection"
          value={currentRej}
          unit=""
          subtext="Membrane barrier efficiency"
          icon={ShieldCheck}
        />
      </div>

      {/* Recommended Action & Alerts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recommendation Panel */}
        <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
            <Zap className="w-4 h-4 text-teal-400" />
            <span>Prescriptive Recommendation</span>
          </h2>

          <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
            <div className="text-xs font-semibold text-teal-400 font-mono uppercase">
              {latestDiagnosis?.explanation?.recommended_action?.replace(/_/g, ' ') || 'CONTINUE NORMAL OPERATION'}
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              {latestDiagnosis?.explanation?.action_summary || 'System is operating within expected nominal boundaries. Continue routine daily monitoring.'}
            </p>
          </div>

          <button
            onClick={() => setActiveTab('maintenance')}
            className="w-full py-2.5 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white transition flex items-center justify-center gap-2"
          >
            <span>Open Guided Maintenance Center</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Explainability Preview */}
        <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4 lg:col-span-2">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
              Diagnostic Explainability Signals
            </h2>
            <button
              onClick={() => setActiveTab('diagnostics')}
              className="text-xs text-teal-400 hover:underline font-medium"
            >
              View Full Breakdown →
            </button>
          </div>

          <div className="space-y-2.5">
            {latestDiagnosis?.explanation?.contributing_factors?.slice(0, 3).map((f, i) => (
              <div key={i} className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-white">{f.factor}</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono ${
                      f.direction === 'negative' ? 'bg-rose-500/10 text-rose-400' : 'bg-slate-800 text-slate-300'
                    }`}>
                      {f.observed_value}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1 leading-relaxed">{f.description}</p>
                </div>
              </div>
            )) || (
              <p className="text-xs text-slate-500 italic">No diagnostic factors calculated yet.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
