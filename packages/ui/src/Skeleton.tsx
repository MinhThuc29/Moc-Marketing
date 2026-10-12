import React from 'react';

export interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'rectangular' | 'circular';
  width?: string | number;
  height?: string | number;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  className = '',
  variant = 'rectangular',
  width,
  height,
}) => {
  const variantClass = {
    text: 'h-4 rounded',
    rectangular: 'rounded-lg',
    circular: 'rounded-full',
  }[variant];

  const style: React.CSSProperties = {
    width,
    height,
  };

  return (
    <div
      className={`animate-pulse bg-slate-200/80 ${variantClass} ${className}`}
      style={style}
    />
  );
};
