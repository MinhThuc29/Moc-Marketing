export * from './Button';
export * from './Input';
export * from './Select';
export * from './Badge';
export * from './Skeleton';
export * from './EmptyState';
export * from './ErrorState';
export * from './Dialog';
export * from './ConfirmDialog';
export * from './Drawer';
export * from './Pagination';
export * from './DataTable';
export * from './StatCard';
export * from './ChartCard';

// Re-export Card from previous version
import React from 'react';

export interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
}

export const Card: React.FC<CardProps> = ({ children, className = '', title }) => {
  return (
    <div className={`bg-white rounded-xl border border-slate-200/90 shadow-xs overflow-hidden ${className}`}>
      {title && (
        <div className="px-6 py-4 border-b border-slate-100 font-semibold text-slate-800 text-sm">
          {title}
        </div>
      )}
      <div className="p-6">{children}</div>
    </div>
  );
};
