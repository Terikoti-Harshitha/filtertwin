import React from 'react';
import { Cpu } from 'lucide-react';

export default function SimulatedDataBadge({ className = '' }) {
  return (
    <div
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold tracking-wide uppercase bg-amber-500/10 text-amber-400 border border-amber-500/30 ${className}`}
      title="This system operates on mathematical simulation models; not physical purifier telemetry."
    >
      <Cpu className="w-3.5 h-3.5 animate-pulse text-amber-400" />
      <span>SIMULATED DATA</span>
    </div>
  );
}
