'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Badge, Button } from '@moc-healthy/ui';
import { useRouter } from 'next/navigation';
import { alertsApi } from '../../lib/api';
import type { SmartAlertSummaryResponse, SmartAlertItem } from '@moc-healthy/contracts';

export interface TopbarProps {
  onToggleMobileMenu: () => void;
}

export const Topbar: React.FC<TopbarProps> = ({ onToggleMobileMenu }) => {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [alertSummary, setAlertSummary] = useState<SmartAlertSummaryResponse | null>(null);
  const [loadingAlerts, setLoadingAlerts] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const fetchAlerts = async () => {
    try {
      setLoadingAlerts(true);
      const data = await alertsApi.getSummary();
      setAlertSummary(data);
    } catch (err) {
      console.warn('Failed to fetch smart alert summary:', err);
    } finally {
      setLoadingAlerts(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    // Poll every 60s
    const timer = setInterval(fetchAlerts, 60000);
    return () => clearInterval(timer);
  }, []);

  const handleAcknowledge = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await alertsApi.acknowledge(id);
      await fetchAlerts();
    } catch (err) {
      console.error('Error acknowledging alert:', err);
    }
  };

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  const totalActive = alertSummary?.total_active ?? 0;
  const criticalCount = alertSummary?.critical ?? 0;
  const warningCount = alertSummary?.warning ?? 0;

  return (
    <header className="h-16 bg-white border-b border-slate-200/90 px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30">
      {/* Left: Mobile hamburger + Global Search */}
      <div className="flex items-center space-x-3 sm:space-x-4 flex-1 max-w-md">
        <button
          onClick={onToggleMobileMenu}
          className="lg:hidden p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition"
          aria-label="Mở menu điều hướng"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        {/* Global Search Placeholder */}
        <div className="relative w-full">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            type="text"
            readOnly
            placeholder="Tìm nhanh SKU, đơn hàng, chiến dịch... (Ctrl+K)"
            className="w-full text-xs bg-slate-50 border border-slate-200 pl-9 pr-12 py-2 rounded-lg cursor-pointer hover:border-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-500 text-slate-600 transition"
          />
          <div className="absolute inset-y-0 right-0 pr-2.5 flex items-center pointer-events-none">
            <kbd className="px-1.5 py-0.5 text-[10px] font-semibold text-slate-400 bg-white border border-slate-200 rounded">
              ⌘K
            </kbd>
          </div>
        </div>
      </div>

      {/* Right: Quick Actions, Notifications, User Menu */}
      <div className="flex items-center space-x-3">
        {/* Notification Button */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg relative transition focus:outline-none"
            aria-label="Thông báo hệ thống"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            {totalActive > 0 && (
              <span
                className={`absolute top-1 right-1 min-w-[18px] h-[18px] px-1 text-[10px] font-bold text-white rounded-full flex items-center justify-center ring-2 ring-white ${
                  criticalCount > 0 ? 'bg-rose-500 animate-pulse' : 'bg-amber-500'
                }`}
              >
                {totalActive > 9 ? '9+' : totalActive}
              </span>
            )}
          </button>

          {/* Notifications Dropdown */}
          {showNotifications && (
            <div className="absolute right-0 mt-2 w-84 sm:w-96 bg-white rounded-xl shadow-xl border border-slate-200 py-3 z-50 animate-in fade-in zoom-in-95">
              <div className="px-4 pb-2.5 border-b border-slate-100 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-800">Cảnh báo thông minh</span>
                  {totalActive > 0 && (
                    <span className="px-1.5 py-0.5 text-[10px] font-semibold bg-rose-50 text-rose-700 rounded-full border border-rose-200">
                      {totalActive} hoạt động
                    </span>
                  )}
                </div>
                <button
                  onClick={fetchAlerts}
                  disabled={loadingAlerts}
                  className="text-[11px] text-emerald-600 hover:text-emerald-700 font-medium"
                >
                  {loadingAlerts ? 'Đang tải...' : 'Làm mới'}
                </button>
              </div>

              <div className="py-2 max-h-80 overflow-y-auto divide-y divide-slate-100">
                {alertSummary?.recent_alerts && alertSummary.recent_alerts.length > 0 ? (
                  alertSummary.recent_alerts.map((alert) => (
                    <div
                      key={alert.id}
                      className="p-3 hover:bg-slate-50 transition flex items-start gap-3 cursor-pointer"
                      onClick={() => {
                        setShowNotifications(false);
                        if (alert.action_url) {
                          router.push(alert.action_url);
                        } else {
                          router.push('/ai-studio');
                        }
                      }}
                    >
                      <span className="text-base flex-shrink-0 mt-0.5">
                        {alert.severity === 'CRITICAL' ? '🚨' : alert.severity === 'WARNING' ? '⚠️' : 'ℹ️'}
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-1">
                          <p className="text-xs font-semibold text-slate-800 truncate">
                            {alert.title}
                          </p>
                          <span
                            className={`text-[9px] font-bold px-1.5 py-0.2 rounded uppercase ${
                              alert.severity === 'CRITICAL'
                                ? 'bg-rose-100 text-rose-700'
                                : alert.severity === 'WARNING'
                                ? 'bg-amber-100 text-amber-700'
                                : 'bg-blue-100 text-blue-700'
                            }`}
                          >
                            {alert.severity}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-600 line-clamp-2 mt-0.5">
                          {alert.message}
                        </p>
                        <div className="flex items-center justify-between mt-1 text-[10px] text-slate-400">
                          <span>{new Date(alert.created_at).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}</span>
                          {alert.status === 'ACTIVE' && (
                            <button
                              onClick={(e) => handleAcknowledge(alert.id, e)}
                              className="text-slate-500 hover:text-emerald-600 font-medium"
                            >
                              Đánh dấu đã xem
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="py-6 text-center text-xs text-slate-400">
                    <span className="text-xl block mb-1">✅</span>
                    Hệ thống hoạt động bình thường, không có cảnh báo rủi ro nào.
                  </div>
                )}
              </div>

              <div className="px-4 pt-2 border-t border-slate-100 flex items-center justify-between">
                <button
                  onClick={() => {
                    setShowNotifications(false);
                    router.push('/ai-studio');
                  }}
                  className="text-xs font-semibold text-emerald-700 hover:text-emerald-800 transition"
                >
                  Xem Trung tâm AI Studio & Khuyến nghị →
                </button>
              </div>
            </div>
          )}
        </div>

        {/* User Menu */}
        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center space-x-2 p-1.5 rounded-lg hover:bg-slate-100 transition focus:outline-none"
          >
            <div className="w-8 h-8 rounded-full bg-emerald-700 text-white font-bold text-xs flex items-center justify-center">
              {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'M'}
            </div>
            <div className="hidden sm:block text-left">
              <span className="block text-xs font-bold text-slate-800 leading-tight">
                {user?.full_name}
              </span>
              <span className="block text-[10px] text-slate-400">
                {user?.roles?.[0] || 'User'}
              </span>
            </div>
          </button>

          {/* User Dropdown */}
          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-56 bg-white rounded-xl shadow-lg border border-slate-100 py-2 z-50 animate-in fade-in zoom-in-95">
              <div className="px-4 py-2 border-b border-slate-100">
                <p className="text-xs font-bold text-slate-900">{user?.full_name}</p>
                <p className="text-[11px] text-slate-500 truncate">{user?.email}</p>
                <div className="flex gap-1 mt-1">
                  {user?.roles?.map((r) => (
                    <Badge key={r} variant="success" size="sm">
                      {r}
                    </Badge>
                  ))}
                </div>
              </div>

              <div className="py-1">
                <button
                  onClick={() => router.push('/settings')}
                  className="w-full text-left px-4 py-2 text-xs text-slate-700 hover:bg-slate-50 transition"
                >
                  Cài đặt tài khoản
                </button>
              </div>

              <div className="border-t border-slate-100 pt-1">
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-4 py-2 text-xs text-rose-600 font-semibold hover:bg-rose-50 transition"
                >
                  Đăng xuất
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
