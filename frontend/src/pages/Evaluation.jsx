import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  Download,
  Play,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Percent,
  RefreshCw
} from 'lucide-react';
import api from '../services/api';
import SimulatedDataBadge from '../components/common/SimulatedDataBadge';

export default function Evaluation() {
  const [evalData, setEvalData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [runningEval, setRunningEval] = useState(false);
  const [error, setError] = useState(null);

  const loadEvaluation = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getLatestEvaluation();
      setEvalData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvaluation();
  }, []);

  const handleRunFreshEvaluation = async () => {
    setRunningEval(true);
    setError(null);
    try {
      const res = await api.triggerEvaluation({ num_scenarios: 200, include_faults: true });
      setEvalData(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setRunningEval(false);
    }
  };

  const reg = evalData?.regression_comparison;
  const inter = evalData?.uncertainty_intervals;
  const anom = evalData?.anomaly_detection;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>Model Evaluation & Benchmark Report</span>
            <SimulatedDataBadge />
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Empirical validation across {evalData?.total_scenarios_evaluated || 200} held-out test scenarios including unseen nonlinear degradation.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <a
            href={api.getReportCsvUrl()}
            download="filtertwin_evaluation_benchmark.csv"
            className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl border border-slate-700 flex items-center gap-1.5 transition"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download CSV Report</span>
          </a>

          <button
            onClick={handleRunFreshEvaluation}
            disabled={runningEval}
            className="px-4 py-2 bg-teal-500 hover:bg-teal-400 text-slate-950 font-semibold text-xs rounded-xl shadow-lg shadow-teal-500/20 transition disabled:opacity-50 flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${runningEval ? 'animate-spin' : ''}`} />
            <span>{runningEval ? 'Evaluating 200 Scenarios...' : 'Run Live Benchmark (200 Runs)'}</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-950/30 border border-rose-800/40 text-rose-300 text-xs font-medium">
          {error}
        </div>
      )}

      {/* Regression Comparison Table */}
      <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
            RUL Regression Performance Comparison
          </h2>
          <span className="text-xs text-slate-500 font-mono">
            {evalData?.total_checkpoint_evaluations} test checkpoints evaluated
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[11px]">
                <th className="py-3 px-4 font-semibold">Model Architecture</th>
                <th className="py-3 px-4 font-semibold">Type</th>
                <th className="py-3 px-4 font-semibold">MAE (Days)</th>
                <th className="py-3 px-4 font-semibold">RMSE (Days)</th>
                <th className="py-3 px-4 font-semibold">Improvement vs Baseline</th>
                <th className="py-3 px-4 font-semibold">Prediction Interval</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              <tr className="hover:bg-slate-800/20">
                <td className="py-3.5 px-4 font-bold text-white font-sans">Fixed-Volume Baseline</td>
                <td className="py-3.5 px-4 text-slate-400 font-sans">Heuristic</td>
                <td className="py-3.5 px-4 text-slate-300 font-bold">{reg?.fixed_volume_baseline?.mae ?? '--'} d</td>
                <td className="py-3.5 px-4 text-slate-400">{reg?.fixed_volume_baseline?.rmse ?? '--'} d</td>
                <td className="py-3.5 px-4 text-slate-500">0.0% (Benchmark)</td>
                <td className="py-3.5 px-4 text-slate-500 font-sans">N/A (Point Estimate)</td>
              </tr>
              <tr className="hover:bg-slate-800/20">
                <td className="py-3.5 px-4 font-bold text-teal-300 font-sans">Multivariable Linear Regression</td>
                <td className="py-3.5 px-4 text-slate-400 font-sans">Ridge Regularized</td>
                <td className="py-3.5 px-4 text-teal-300 font-bold">{reg?.linear_regression?.mae ?? '--'} d</td>
                <td className="py-3.5 px-4 text-slate-300">{reg?.linear_regression?.rmse ?? '--'} d</td>
                <td className="py-3.5 px-4 text-emerald-400 font-bold">+{reg?.linear_regression?.improvement_pct ?? '--'}%</td>
                <td className="py-3.5 px-4 text-slate-400 font-sans">80% Quantile</td>
              </tr>
              <tr className="hover:bg-slate-800/20 bg-teal-950/10">
                <td className="py-3.5 px-4 font-bold text-teal-200 font-sans">Gradient Boosted Trees</td>
                <td className="py-3.5 px-4 text-slate-300 font-sans">HistGradientBoosting</td>
                <td className="py-3.5 px-4 text-teal-200 font-bold">{reg?.gradient_boosting?.mae ?? '--'} d</td>
                <td className="py-3.5 px-4 text-slate-300">{reg?.gradient_boosting?.rmse ?? '--'} d</td>
                <td className="py-3.5 px-4 text-emerald-400 font-bold">+{reg?.gradient_boosting?.improvement_pct ?? '--'}%</td>
                <td className="py-3.5 px-4 text-teal-300 font-sans">80% Quantile [Q10 - Q90]</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Uncertainty & Anomaly Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Prediction Interval Coverage */}
        <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
            Prediction Interval Coverage (PICP)
          </h2>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-1">
              <span className="text-[11px] text-slate-500 uppercase font-semibold">Empirical Coverage</span>
              <div className="text-2xl font-bold font-mono text-teal-400">{inter?.picp_coverage_pct ?? '--'}%</div>
              <p className="text-[11px] text-slate-500">Nominal 80% coverage target</p>
            </div>
            <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-1">
              <span className="text-[11px] text-slate-500 uppercase font-semibold">Mean Interval Width</span>
              <div className="text-2xl font-bold font-mono text-slate-200">{inter?.average_interval_width ?? '--'} d</div>
              <p className="text-[11px] text-slate-500">Average [Q90 - Q10] spread</p>
            </div>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Coverage is measured strictly on held-out evaluation scenarios that were never seen during model training or quantile calibration.
          </p>
        </div>

        {/* Anomaly Detection Metrics */}
        <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
            Anomaly Detection Performance
          </h2>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
            <div className="p-3 rounded-2xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">Precision</span>
              <div className="text-xl font-bold font-mono text-teal-300 mt-0.5">{anom?.precision ?? '--'}</div>
            </div>
            <div className="p-3 rounded-2xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">Recall</span>
              <div className="text-xl font-bold font-mono text-teal-300 mt-0.5">{anom?.recall ?? '--'}</div>
            </div>
            <div className="p-3 rounded-2xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">F1-Score</span>
              <div className="text-xl font-bold font-mono text-teal-300 mt-0.5">{anom?.f1_score ?? '--'}</div>
            </div>
            <div className="p-3 rounded-2xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">False Alerts</span>
              <div className="text-xl font-bold font-mono text-amber-400 mt-0.5">{anom?.false_alert_rate_pct ?? '--'}%</div>
            </div>
          </div>

          {/* Per-Fault Recall Breakdown */}
          <div className="space-y-2 pt-2 border-t border-slate-800">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Per-Fault Detection Breakdown</span>
            <div className="space-y-1.5">
              {anom?.per_fault_detection_pct && Object.entries(anom.per_fault_detection_pct).map(([fault, pct]) => (
                <div key={fault} className="flex items-center justify-between text-xs">
                  <span className="font-mono text-slate-300">{fault.replace('_', ' ')}</span>
                  <span className={`font-mono font-bold ${pct >= 90 ? 'text-emerald-400' : pct >= 60 ? 'text-amber-400' : 'text-rose-400'}`}>
                    {pct}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
