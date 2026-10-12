import React from 'react';
import { Badge } from './Badge';

export interface StatCardProps {
  title: string;
  value: string | number;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  period?: string;
  icon?: React.ReactNode;
  className?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  change,
  changeType = 'neutral',
  period,
  icon,
  className = '',
}) => {
  const badgeVariant = {
    positive: 'success' as const,
    negative: 'danger' as const,
    neutral: 'neutral' as const,
  }[changeType];

  return (
    <div
      className={`bg-white rounded-xl border border-slate-200/90 p-5 shadow-xs transition-shadow hover:shadow-sm ${className}`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{title}</span>
        {icon && (
          <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center text-sm font-semibold">
            {icon}
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline justify-between">
        <span className="text-2xl font-extrabold text-slate-900 tracking-tight">{value}</span>
        {change && (
          <Badge variant={badgeVariant} size="sm">
            {changeType === 'positive' && '+'}
            {change}
          </Badge>
        )}
      </div>

      {period && <p className="text-[11px] text-slate-400 mt-2 font-medium">{period}</p>}
    </div>
  );
};
