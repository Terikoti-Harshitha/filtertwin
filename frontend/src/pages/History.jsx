import React, { useState } from 'react';
import {
  Download,
  FileSpreadsheet,
  FileText,
  Clock,
  Layers,
  Database,
  CheckCircle2
} from 'lucide-react';
import { usePurifier } from '../context/PurifierContext';
import api from '../services/api';
import SimulatedDataBadge from '../components/common/SimulatedDataBadge';

export default function History() {
  const { readings, selectedPurifier, activeSimulation, latestDiagnosis } = usePurifier();

  const handleDownloadTelemetryCsv = () => {
    if (!readings || readings.length === 0) {
      alert('No telemetry readings available to download.');
      return;
    }

    const headers = ['simulated_day', 'timestamp', 'flow_rate_lpm', 'inlet_tds_ppm', 'outlet_tds_ppm', 'rejection_percentage', 'cumulative_volume_l', 'sensor_status'];
    const rows = readings.map(r => [
      r.simulated_day,
      r.timestamp,
      r.flow_rate_lpm ?? '',
      r.inlet_tds_ppm ?? '',
      r.outlet_tds_ppm ?? '',
      r.rejection_percentage ?? '',
      r.cumulative_volume_l ?? '',
      r.sensor_status ?? 'normal'
    ]);

    const csvContent = [headers.join(','), ...rows.map(row => row.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `filtertwin_telemetry_${selectedPurifier?.name?.replace(/\s+/g, '_') || 'purifier'}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleDownloadDiagnosticReportJson = () => {
    if (!latestDiagnosis) {
      alert('No diagnostic records available to download.');
      return;
    }

    const reportObj = {
      platform: 'FilterTwin Explainable Diagnostics',
      data_nature: 'MATHEMATICALLY SIMULATED TELEMETRY',
      team: 'CoreCraft - Lendi Institute of Engineering and Technology',
      generated_at: new Date().toISOString(),
      purifier_profile: selectedPurifier,
      simulation_run: activeSimulation,
      latest_diagnosis: latestDiagnosis,
    };

    const blob = new Blob([JSON.stringify(reportObj, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'filtertwin_diagnostic_report.json');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>Audit History & Exportable Reports</span>
            <SimulatedDataBadge />
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Export structured telemetry logs, model diagnostics, and held-out benchmark datasets for reproducible analysis.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Card 1: Telemetry CSV */}
        <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4 flex flex-col justify-between">
          <div className="space-y-3">
            <div className="w-10 h-10 rounded-2xl bg-teal-500/10 border border-teal-500/20 flex items-center justify-center text-teal-400">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <h2 className="text-sm font-bold text-white">Time-Series Telemetry (CSV)</h2>
            <p className="text-xs text-slate-400 leading-relaxed">
              Export all {readings.length} observed simulation data points, including daily flow rates, feed/product TDS, and membrane rejection percentage.
            </p>
          </div>

          <button
            onClick={handleDownloadTelemetryCsv}
            disabled={readings.length === 0}
            className="w-full py-2.5 px-4 bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 rounded-xl border border-slate-700 transition flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Telemetry CSV</span>
          </button>
        </div>

        {/* Card 2: Full Diagnostic Report JSON */}
        <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4 flex flex-col justify-between">
          <div className="space-y-3">
            <div className="w-10 h-10 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <FileText className="w-5 h-5" />
            </div>
            <h2 className="text-sm font-bold text-white">Full Diagnostic Dossier (JSON)</h2>
            <p className="text-xs text-slate-400 leading-relaxed">
              Complete diagnostic record containing baseline vs ML RUL estimates, 80% quantile intervals, anomaly states, and coefficient contributions.
            </p>
          </div>

          <button
            onClick={handleDownloadDiagnosticReportJson}
            disabled={!latestDiagnosis}
            className="w-full py-2.5 px-4 bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 rounded-xl border border-slate-700 transition flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Diagnostic JSON</span>
          </button>
        </div>

        {/* Card 3: Model Evaluation Benchmark CSV */}
        <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4 flex flex-col justify-between">
          <div className="space-y-3">
            <div className="w-10 h-10 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <Database className="w-5 h-5" />
            </div>
            <h2 className="text-sm font-bold text-white">200-Scenario Benchmark (CSV)</h2>
            <p className="text-xs text-slate-400 leading-relaxed">
              Official held-out evaluation summary comparing MAE, RMSE, interval coverage (PICP), anomaly recall, and false alert rates.
            </p>
          </div>

          <a
            href={api.getReportCsvUrl()}
            download="filtertwin_evaluation_benchmark.csv"
            className="w-full py-2.5 px-4 bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-xs rounded-xl shadow-lg shadow-teal-500/20 transition flex items-center justify-center gap-2 text-center"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Benchmark CSV</span>
          </a>
        </div>
      </div>

      {/* Raw Telemetry Preview Table */}
      <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
          Recent Telemetry Observation Log
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[11px]">
                <th className="py-2.5 px-3 font-semibold">Sim Day</th>
                <th className="py-2.5 px-3 font-semibold">Volume (L)</th>
                <th className="py-2.5 px-3 font-semibold">Flow Rate</th>
                <th className="py-2.5 px-3 font-semibold">Feed TDS</th>
                <th className="py-2.5 px-3 font-semibold">Permeate TDS</th>
                <th className="py-2.5 px-3 font-semibold">Salt Rejection</th>
                <th className="py-2.5 px-3 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {readings.slice(-10).reverse().map((r, i) => (
                <tr key={i} className="hover:bg-slate-800/20">
                  <td className="py-2.5 px-3 font-bold text-white font-sans">{r.simulated_day}</td>
                  <td className="py-2.5 px-3 text-slate-300">{Math.round(r.cumulative_volume_l)} L</td>
                  <td className="py-2.5 px-3 text-teal-300">{r.flow_rate_lpm != null ? `${r.flow_rate_lpm.toFixed(2)} LPM` : '--'}</td>
                  <td className="py-2.5 px-3 text-slate-400">{r.inlet_tds_ppm != null ? `${r.inlet_tds_ppm.toFixed(0)} ppm` : '--'}</td>
                  <td className="py-2.5 px-3 text-cyan-300">{r.outlet_tds_ppm != null ? `${r.outlet_tds_ppm.toFixed(1)} ppm` : '--'}</td>
                  <td className="py-2.5 px-3 text-slate-300">{r.rejection_percentage != null ? `${r.rejection_percentage.toFixed(1)}%` : '--'}</td>
                  <td className="py-2.5 px-3">
                    <span className={`text-[10px] px-2 py-0.5 rounded font-sans uppercase font-bold ${
                      r.sensor_status === 'normal'
                        ? 'bg-emerald-500/10 text-emerald-400'
                        : r.sensor_status === 'insufficient_data'
                        ? 'bg-slate-800 text-slate-400'
                        : 'bg-rose-500/10 text-rose-400'
                    }`}>
                      {r.sensor_status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
