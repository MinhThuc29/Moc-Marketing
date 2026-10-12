'use client';

import React from 'react';
import { Badge, Button } from '@moc-healthy/ui';
import { SmartAlertItem } from '@moc-healthy/contracts';

interface SmartAlertsBannerProps {
  alerts: SmartAlertItem[];
  onAcknowledge: (alertId: string) => void;
  onResolve: (alertId: string) => void;
  onRefresh: () => void;
  isScanning?: boolean;
}

export const SmartAlertsBanner: React.FC<SmartAlertsBannerProps> = ({
  alerts,
  onAcknowledge,
  onResolve,
  onRefresh,
  isScanning = false,
}) => {
  if (!alerts || alerts.length === 0) return null;

  const criticalAlerts = alerts.filter((a) => a.severity === 'CRITICAL');
  const warningAlerts = alerts.filter((a) => a.severity === 'WARNING');
  const otherAlerts = alerts.filter((a) => a.severity !== 'CRITICAL' && a.severity !== 'WARNING');

  const displayAlerts = [...criticalAlerts, ...warningAlerts, ...otherAlerts].slice(0, 4);

  return (
    <div className="bg-slate-900 text-white rounded-xl p-4 mb-6 shadow-md border border-slate-800">
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <span className="flex h-2.5 w-2.5 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-500"></span>
          </span>
          <h4 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
            🚨 Trung Tâm Cảnh Báo Thông Minh Thời Gian Thực (Smart Alerts)
          </h4>
          <span className="bg-rose-950/80 text-rose-300 text-xs px-2 py-0.5 rounded-full font-bold border border-rose-800">
            {alerts.length} cảnh báo đang mở
          </span>
        </div>

        <button
          onClick={onRefresh}
          disabled={isScanning}
          className="text-xs text-slate-400 hover:text-white flex items-center gap-1 transition"
        >
          <span>🔄</span>
          <span>{isScanning ? 'Đang quét...' : 'Quét lại hệ thống'}</span>
        </button>
      </div>

      <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
        {displayAlerts.map((alert) => (
          <div
            key={alert.id}
            className={`p-3 rounded-lg border flex flex-col justify-between transition-all ${
              alert.severity === 'CRITICAL'
                ? 'bg-rose-950/30 border-rose-800/80 text-rose-100'
                : alert.severity === 'WARNING'
                ? 'bg-amber-950/30 border-amber-800/80 text-amber-100'
                : 'bg-slate-800/60 border-slate-700 text-slate-200'
            }`}
          >
            <div>
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs">
                    {alert.severity === 'CRITICAL' ? '⛔' : alert.severity === 'WARNING' ? '⚠️' : 'ℹ️'}
                  </span>
                  <span className="text-xs font-bold leading-tight">
                    {alert.title}
                  </span>
                </div>
                <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-black/40">
                  {alert.severity}
                </span>
              </div>
              <p className="mt-1.5 text-xs text-slate-300 leading-relaxed">
                {alert.message}
              </p>
            </div>

            <div className="mt-3 pt-2 border-t border-white/10 flex items-center justify-between gap-2">
              <span className="text-[10px] text-slate-400">
                {new Date(alert.created_at).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
              </span>
              <div className="flex items-center gap-1.5">
                {alert.action_url && (
                  <a
                    href={alert.action_url}
                    className="text-[11px] text-emerald-400 hover:text-emerald-300 font-semibold underline px-1.5 py-0.5"
                  >
                    Xử lý ngay →
                  </a>
                )}
                {alert.status === 'ACTIVE' && (
                  <button
                    onClick={() => onAcknowledge(alert.id)}
                    className="text-[11px] px-2 py-0.5 rounded bg-white/10 hover:bg-white/20 text-slate-200 font-medium transition"
                  >
                    Đã xem
                  </button>
                )}
                <button
                  onClick={() => onResolve(alert.id)}
                  className="text-[11px] px-2 py-0.5 rounded bg-emerald-600/80 hover:bg-emerald-600 text-white font-medium transition"
                >
                  Xong ✓
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
