import React from 'react';

export default function MetricCard({
  title,
  value,
  unit = '',
  subtext = '',
  icon: Icon,
  variant = 'default',
  badge = null,
}) {
  const variantStyles = {
    default: 'bg-slate-900/80 border-slate-800 text-slate-100',
    primary: 'bg-teal-950/30 border-teal-800/40 text-teal-200',
    warning: 'bg-amber-950/30 border-amber-800/40 text-amber-200',
    danger: 'bg-rose-950/30 border-rose-800/40 text-rose-200',
  };

  return (
    <div className={`p-5 rounded-2xl border backdrop-blur-sm transition-all hover:border-slate-700 shadow-sm ${variantStyles[variant]}`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium tracking-wider text-slate-400 uppercase">{title}</span>
        {badge}
        {Icon && <Icon className="w-5 h-5 text-slate-400" />}
      </div>
      <div className="flex items-baseline gap-1.5">
        <span className="text-2xl font-bold font-mono tracking-tight text-white">{value}</span>
        {unit && <span className="text-xs text-slate-400 font-medium">{unit}</span>}
      </div>
      {subtext && <p className="mt-2 text-xs text-slate-400 line-clamp-1">{subtext}</p>}
    </div>
  );
}
