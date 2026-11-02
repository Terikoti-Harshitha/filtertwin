import React from 'react';
import { Droplets, RefreshCw } from 'lucide-react';
import { usePurifier } from '../../context/PurifierContext';
import SimulatedDataBadge from '../common/SimulatedDataBadge';
import StatusIndicator from '../common/StatusIndicator';

export default function Navbar() {
  const { purifiers, selectedPurifier, setSelectedPurifier, latestDiagnosis, refreshDiagnosis, loading } = usePurifier();

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/60 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-teal-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-teal-500/20">
            <Droplets className="w-5 h-5 text-slate-950 font-bold" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-base tracking-tight text-white">FilterTwin</span>
              <span className="text-[10px] font-mono text-teal-400 bg-teal-500/10 px-1.5 py-0.5 rounded border border-teal-500/20">v1.0</span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">Explainable Filter Diagnostics & Guided Maintenance</p>
          </div>
        </div>

        <div className="hidden lg:block h-5 w-[1px] bg-slate-800 mx-2"></div>

        {/* Purifier Profile Selector */}
        <div className="hidden md:flex items-center gap-2">
          <label className="text-xs text-slate-400 font-medium">Profile:</label>
          <select
            value={selectedPurifier?.id || ''}
            onChange={(e) => {
              const p = purifiers.find(x => x.id === e.target.value);
              if (p) setSelectedPurifier(p);
            }}
            className="bg-slate-950 border border-slate-700 text-xs rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-teal-500"
          >
            {purifiers.map(p => (
              <option key={p.id} value={p.id}>{p.name} ({p.location})</option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <SimulatedDataBadge />

        {latestDiagnosis?.diagnosis && (
          <StatusIndicator category={latestDiagnosis.diagnosis.category} size="md" />
        )}

        <button
          onClick={refreshDiagnosis}
          disabled={loading}
          title="Refresh real-time diagnostics"
          className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>

        <div className="hidden xl:flex flex-col text-right pl-2 border-l border-slate-800">
          <span className="text-[11px] font-semibold text-slate-300">Team CoreCraft</span>
          <span className="text-[10px] text-slate-500">Lendi Inst. of Eng. & Tech.</span>
        </div>
      </div>
    </header>
  );
}
