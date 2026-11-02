import React from 'react';
import {
  BrainCircuit,
  TrendingDown,
  AlertTriangle,
  HelpCircle,
  CheckCircle2,
  BarChart,
  Zap,
  ArrowRight,
  ShieldAlert,
  Info
} from 'lucide-react';
import { usePurifier } from '../context/PurifierContext';
import StatusIndicator from '../components/common/StatusIndicator';
import SimulatedDataBadge from '../components/common/SimulatedDataBadge';

export default function Diagnostics({ setActiveTab }) {
  const { latestDiagnosis, refreshDiagnosis, loading } = usePurifier();

  const baseline = latestDiagnosis?.baseline_prediction;
  const linear = latestDiagnosis?.linear_prediction;
  const gb = latestDiagnosis?.gradient_boosting_prediction;
  const interval = latestDiagnosis?.uncertainty_interval;
  const diag = latestDiagnosis?.diagnosis;
  const expl = latestDiagnosis?.explanation;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>Diagnostics & Predictive Intelligence</span>
            <SimulatedDataBadge />
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Multivariable remaining useful life models, calibrated quantile prediction intervals, and explainable failure factors.
          </p>
        </div>

        <button
          onClick={refreshDiagnosis}
          disabled={loading}
          className="px-4 py-2 bg-teal-500 hover:bg-teal-400 text-slate-950 font-semibold text-xs rounded-xl shadow-lg shadow-teal-500/20 transition disabled:opacity-50 flex items-center gap-1.5"
        >
          <BrainCircuit className="w-4 h-4" />
          <span>{loading ? 'Evaluating...' : 'Re-Evaluate Diagnostics'}</span>
        </button>
      </div>

      {/* Model RUL Comparison Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Model 1: Fixed-Volume Baseline */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3 relative">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Model 1: Baseline</span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">Heuristic</span>
          </div>
          <div className="text-sm font-semibold text-white">Fixed-Volume Benchmark</div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-3xl font-extrabold font-mono text-slate-200">{baseline?.rul_days ?? '--'}</span>
            <span className="text-xs text-slate-400">days</span>
          </div>
          <p className="text-[11px] text-slate-500">
            Static rated capacity countdown ({baseline?.rul_litres ?? '--'} L remaining). Does not adapt to actual filter performance or TDS loading.
          </p>
        </div>

        {/* Model 2: Multivariable Linear Regression */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-teal-400 uppercase tracking-wider">Model 2: Statistical</span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-teal-500/10 text-teal-400 font-mono">Adaptive ML</span>
          </div>
          <div className="text-sm font-semibold text-white">Multivariable Linear Regression</div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-3xl font-extrabold font-mono text-teal-300">{linear?.rul_days ?? '--'}</span>
            <span className="text-xs text-teal-400">days</span>
          </div>
          <p className="text-[11px] text-slate-400">
            Standardized linear regression on flow ratio, TDS load, and rejection slope ({linear?.rul_litres ?? '--'} L equivalent).
          </p>
        </div>

        {/* Model 3: Gradient Boosted Trees */}
        <div className="p-5 rounded-2xl bg-teal-950/20 border border-teal-800/40 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-teal-300 uppercase tracking-wider">Model 3: Ensemble</span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-teal-400/20 text-teal-200 font-mono font-bold">Nonlinear ML</span>
          </div>
          <div className="text-sm font-semibold text-white">Gradient Boosted Regressor</div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-3xl font-extrabold font-mono text-teal-200">{gb?.rul_days ?? '--'}</span>
            <span className="text-xs text-teal-300">days</span>
          </div>
          <p className="text-[11px] text-teal-200/70">
            Learns nonlinear relationships and multi-signal interactions between hydraulic flow degradation and cumulative salt loading.
          </p>
        </div>
      </div>

      {/* Uncertainty Prediction Interval Card */}
      <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <Zap className="w-4 h-4 text-teal-400" />
              <span>Calibrated 80% Prediction Uncertainty Interval</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Trained across 10th (lower), 50th (median), and 90th (upper) percentiles using quantile gradient boosting.
            </p>
          </div>
          <div className="text-xs font-mono text-slate-400">
            Empirical Coverage: <span className="font-bold text-teal-400">{interval?.historical_empirical_coverage_pct ?? 85}%</span>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-950 border border-slate-800 space-y-4">
          <div className="grid grid-cols-3 text-center gap-4">
            <div>
              <div className="text-xs text-slate-500 font-medium uppercase">10th Percentile (Conservative)</div>
              <div className="text-2xl font-bold font-mono text-amber-400 mt-1">{interval?.rul_lower_days ?? '--'} d</div>
              <div className="text-[11px] text-slate-500">{interval?.rul_lower_litres ?? '--'} L</div>
            </div>
            <div className="border-x border-slate-800">
              <div className="text-xs text-teal-400 font-bold uppercase">50th Percentile (Median)</div>
              <div className="text-3xl font-extrabold font-mono text-teal-300 mt-1">{interval?.rul_median_days ?? '--'} d</div>
              <div className="text-[11px] text-teal-400/80">{interval?.rul_median_litres ?? '--'} L</div>
            </div>
            <div>
              <div className="text-xs text-slate-500 font-medium uppercase">90th Percentile (Optimistic)</div>
              <div className="text-2xl font-bold font-mono text-cyan-400 mt-1">{interval?.rul_upper_days ?? '--'} d</div>
              <div className="text-[11px] text-slate-500">{interval?.rul_upper_litres ?? '--'} L</div>
            </div>
          </div>

          {/* Visual Band */}
          <div className="space-y-1.5 pt-2">
            <div className="flex justify-between text-[11px] text-slate-400 font-mono">
              <span>Lower Bound ({interval?.rul_lower_days}d)</span>
              <span>Interval Width: {interval?.interval_width_days} days</span>
              <span>Upper Bound ({interval?.rul_upper_days}d)</span>
            </div>
            <div className="h-3 w-full bg-slate-900 rounded-full overflow-hidden flex relative">
              <div className="h-full bg-teal-500/40 rounded-full w-full"></div>
            </div>
          </div>
        </div>
      </div>

      {/* Diagnostic State & Explainability */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Diagnostic Assessment */}
        <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
            Operating Classification
          </h2>

          <div className="space-y-3">
            <StatusIndicator category={diag?.category || 'NORMAL'} size="lg" />

            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
              <div className="text-xs font-semibold text-slate-300">Diagnostic Summary</div>
              <p className="text-xs text-slate-400 leading-relaxed">
                {diag?.message || 'Readings are within nominal limits.'}
              </p>
            </div>

            <div className="space-y-1">
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Observed Evidence</div>
              <ul className="space-y-1">
                {diag?.evidence?.map((ev, i) => (
                  <li key={i} className="text-xs text-slate-300 flex items-start gap-1.5">
                    <span className="text-teal-400">•</span>
                    <span>{ev}</span>
                  </li>
                )) || <li className="text-xs text-slate-500">None</li>}
              </ul>
            </div>
          </div>
        </div>

        {/* Explainability Factors */}
        <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4 lg:col-span-2">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
              Factor Contribution Breakdown
            </h2>
            <span className="text-xs text-slate-500">Derived from model coefficients</span>
          </div>

          <div className="space-y-3">
            {expl?.contributing_factors?.map((factor, i) => (
              <div key={i} className="p-4 rounded-2xl bg-slate-950 border border-slate-800/80 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-white">{factor.factor}</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-medium ${
                      factor.direction === 'negative'
                        ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        : factor.direction === 'mild_negative'
                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                        : 'bg-slate-800 text-slate-300 border border-slate-700'
                    }`}>
                      {factor.observed_value}
                    </span>
                  </div>
                  <span className="text-[11px] font-mono text-slate-500">
                    Impact: {factor.impact_magnitude?.toFixed(2) || '0.00'}
                  </span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">{factor.description}</p>
              </div>
            )) || (
              <div className="text-xs text-slate-500 italic p-4 text-center">No factors available.</div>
            )}
          </div>

          <p className="text-[11px] text-slate-500 italic border-t border-slate-800 pt-3">
            {expl?.disclaimer}
          </p>
        </div>
      </div>
    </div>
  );
}
