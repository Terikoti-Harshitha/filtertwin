import React, { useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  AreaChart,
  Area,
} from 'recharts';
import { Activity, Droplets, Gauge, ShieldCheck, Eye, EyeOff } from 'lucide-react';
import { usePurifier } from '../context/PurifierContext';
import SimulatedDataBadge from '../components/common/SimulatedDataBadge';

export default function Monitoring() {
  const { readings, activeSimulation } = usePurifier();
  const [showGroundTruth, setShowGroundTruth] = useState(false);
  const [selectedWindow, setSelectedWindow] = useState('all');

  const filteredReadings = selectedWindow === '30'
    ? readings.slice(-30)
    : selectedWindow === '60'
    ? readings.slice(-60)
    : readings;

  const chartData = filteredReadings.map((r) => ({
    day: r.simulated_day,
    flow: r.flow_rate_lpm != null ? Number(r.flow_rate_lpm.toFixed(2)) : null,
    inletTds: r.inlet_tds_ppm != null ? Number(r.inlet_tds_ppm.toFixed(1)) : null,
    outletTds: r.outlet_tds_ppm != null ? Number(r.outlet_tds_ppm.toFixed(1)) : null,
    rejection: r.rejection_percentage != null ? Number(r.rejection_percentage.toFixed(1)) : null,
    volume: r.cumulative_volume_l != null ? Math.round(r.cumulative_volume_l) : null,
  }));

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="p-3 bg-slate-900 border border-slate-700 rounded-xl shadow-xl text-xs space-y-1">
          <div className="font-semibold text-slate-300">Simulated Day {label}</div>
          {payload.map((entry, idx) => (
            <div key={idx} style={{ color: entry.color }} className="flex justify-between gap-3 font-mono">
              <span>{entry.name}:</span>
              <span className="font-bold">{entry.value}</span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>Live Telemetry & Sensor Monitoring</span>
            <SimulatedDataBadge />
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time observed sensor signals: permeate flow, dissolved solids, and membrane rejection percentage.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Window Filter */}
          <div className="flex rounded-xl bg-slate-900 border border-slate-800 p-1 text-xs">
            {['30', '60', 'all'].map((w) => (
              <button
                key={w}
                onClick={() => setSelectedWindow(w)}
                className={`px-3 py-1 rounded-lg font-medium transition ${
                  selectedWindow === w ? 'bg-teal-500/20 text-teal-300' : 'text-slate-400 hover:text-white'
                }`}
              >
                {w === 'all' ? 'Full Run' : `Last ${w}d`}
              </button>
            ))}
          </div>
        </div>
      </div>

      {chartData.length === 0 ? (
        <div className="p-12 text-center rounded-3xl bg-slate-900/40 border border-slate-800 text-slate-400 text-sm">
          No telemetry readings generated yet. Please launch a simulation run in the Simulator Studio.
        </div>
      ) : (
        <div className="space-y-6">
          {/* Chart 1: Flow Rate & Rejection Efficiency */}
          <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-slate-300">
                <Gauge className="w-4 h-4 text-teal-400" />
                <span>Hydraulic Flow Rate & Salt Rejection %</span>
              </div>
              <span className="text-xs text-slate-400 font-mono">
                Latest: {chartData[chartData.length - 1]?.flow} LPM / {chartData[chartData.length - 1]?.rejection}%
              </span>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="day" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis yAxisId="left" stroke="#14b8a6" domain={[0, 'auto']} tick={{ fontSize: 11 }} unit=" LPM" />
                  <YAxis yAxisId="right" orientation="right" stroke="#38bdf8" domain={[50, 100]} tick={{ fontSize: 11 }} unit="%" />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                  <Line yAxisId="left" type="monotone" dataKey="flow" name="Flow Rate (LPM)" stroke="#14b8a6" strokeWidth={2} dot={false} />
                  <Line yAxisId="right" type="monotone" dataKey="rejection" name="TDS Rejection (%)" stroke="#38bdf8" strokeWidth={2} dot={false} strokeDasharray="4 4" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Chart 2: Inlet TDS vs Outlet Product TDS */}
          <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-slate-300">
                <Droplets className="w-4 h-4 text-cyan-400" />
                <span>Dissolved Solids: Feed TDS vs Product Permeate TDS</span>
              </div>
              <span className="text-xs text-slate-400 font-mono">
                Latest: Feed {chartData[chartData.length - 1]?.inletTds} ppm • Permeate {chartData[chartData.length - 1]?.outletTds} ppm
              </span>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="day" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 11 }} unit=" ppm" />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                  <Area type="monotone" dataKey="inletTds" name="Inlet Feed TDS (ppm)" stroke="#94a3b8" fill="#475569" fillOpacity={0.15} />
                  <Area type="monotone" dataKey="outletTds" name="Purified Product TDS (ppm)" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.3} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Chart 3: Cumulative Water Volume Processed */}
          <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-slate-300">
                <Activity className="w-4 h-4 text-indigo-400" />
                <span>Cumulative Water Volume Processed (Litres)</span>
              </div>
              <span className="text-xs text-slate-400 font-mono">
                Total: {chartData[chartData.length - 1]?.volume} L
              </span>
            </div>

            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="day" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 11 }} unit=" L" />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                  <Line type="monotone" dataKey="volume" name="Cumulative Volume (L)" stroke="#818cf8" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
