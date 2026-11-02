import React from 'react';
import { CheckCircle2, AlertTriangle, AlertOctagon, HelpCircle } from 'lucide-react';

export default function StatusIndicator({ category = 'NORMAL', size = 'md' }) {
  const configs = {
    NORMAL: {
      label: 'Healthy Normal',
      color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
      icon: CheckCircle2,
    },
    GRADUAL_WEAR: {
      label: 'Gradual Wear',
      color: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
      icon: AlertTriangle,
    },
    ABRUPT_ANOMALY: {
      label: 'Abrupt Anomaly',
      color: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
      icon: AlertOctagon,
    },
    INSUFFICIENT_DATA: {
      label: 'Insufficient Data',
      color: 'bg-slate-500/10 text-slate-400 border-slate-500/30',
      icon: HelpCircle,
    },
  };

  const current = configs[category] || configs.NORMAL;
  const Icon = current.icon;

  const sizeStyles = {
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-xs px-3 py-1 gap-1.5 font-medium',
    lg: 'text-sm px-4 py-1.5 gap-2 font-semibold',
  };

  return (
    <div className={`inline-flex items-center rounded-full border ${current.color} ${sizeStyles[size]}`}>
      <Icon className="w-3.5 h-3.5 shrink-0" />
      <span>{current.label}</span>
    </div>
  );
}
