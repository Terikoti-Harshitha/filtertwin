import React from 'react';
import {
  LayoutDashboard,
  Cpu,
  Activity,
  BrainCircuit,
  BarChart3,
  Wrench,
  History,
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'simulator', label: 'Simulator Studio', icon: Cpu },
    { id: 'monitoring', label: 'Live Monitoring', icon: Activity },
    { id: 'diagnostics', label: 'Diagnostics & RUL', icon: BrainCircuit },
    { id: 'evaluation', label: 'Model Evaluation', icon: BarChart3 },
    { id: 'maintenance', label: 'Maintenance Center', icon: Wrench },
    { id: 'history', label: 'History & Reports', icon: History },
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-900/40 backdrop-blur-md flex flex-col justify-between p-4 shrink-0">
      <nav className="space-y-1.5">
        <div className="px-3 py-2 text-[11px] font-bold uppercase tracking-wider text-slate-500">
          Navigation
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all ${
                isActive
                  ? 'bg-teal-500/10 text-teal-400 border border-teal-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-teal-400' : 'text-slate-400'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Engine Status</span>
          <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          Autonomous Python FastAPI + Scikit-Learn predictive engine online.
        </p>
      </div>
    </aside>
  );
}
