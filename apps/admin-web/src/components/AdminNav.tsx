'use client';

import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Badge, Button } from '@moc-healthy/ui';
import { useRouter } from 'next/navigation';

export const AdminNav: React.FC = () => {
  const { user, logout, hasPermission } = useAuth();
  const router = useRouter();

  if (!user) return null;

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  return (
    <header className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between sticky top-0 z-40">
      <div className="flex items-center space-x-8">
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => router.push('/')}>
          <div className="w-8 h-8 rounded-lg bg-emerald-700 flex items-center justify-center text-white font-bold text-lg">
            M
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-800 leading-tight">Mộc Healthy Admin</h1>
            <p className="text-[11px] text-slate-500">AI Commerce & Marketing Hub</p>
          </div>
        </div>

        {/* Permission-aware Nav Links */}
        <nav className="hidden lg:flex items-center space-x-1 text-sm font-medium text-slate-600">
          <button
            onClick={() => router.push('/')}
            className="px-3 py-1.5 rounded-md hover:bg-slate-100 hover:text-slate-900 transition"
          >
            Tổng quan
          </button>

          {hasPermission('product.read') && (
            <button className="px-3 py-1.5 rounded-md hover:bg-slate-100 hover:text-slate-900 transition">
              Sản phẩm
            </button>
          )}

          {hasPermission('inventory.read') && (
            <button className="px-3 py-1.5 rounded-md hover:bg-slate-100 hover:text-slate-900 transition">
              Kho & Lô HSD
            </button>
          )}

          {hasPermission('order.read') && (
            <button className="px-3 py-1.5 rounded-md hover:bg-slate-100 hover:text-slate-900 transition">
              Đơn hàng
            </button>
          )}

          {hasPermission('campaign.create') && (
            <button className="px-3 py-1.5 rounded-md hover:bg-slate-100 hover:text-slate-900 transition">
              Marketing & AI
            </button>
          )}

          {hasPermission('analytics.read') && (
            <button className="px-3 py-1.5 rounded-md hover:bg-slate-100 hover:text-slate-900 transition">
              Báo cáo & Phân bổ
            </button>
          )}

          {hasPermission('user.manage') && (
            <button className="px-3 py-1.5 rounded-md hover:bg-slate-100 hover:text-slate-900 transition">
              Người dùng & Cài đặt
            </button>
          )}
        </nav>
      </div>

      <div className="flex items-center space-x-4">
        <div className="flex flex-col items-end text-right">
          <span className="text-xs font-semibold text-slate-800">{user.full_name}</span>
          <div className="flex gap-1 mt-0.5">
            {user.roles.map((r) => (
              <Badge key={r} variant="success">
                {r}
              </Badge>
            ))}
          </div>
        </div>

        <Button variant="outline" size="sm" onClick={handleLogout}>
          Đăng xuất
        </Button>
      </div>
    </header>
  );
};
