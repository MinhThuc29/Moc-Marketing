'use client';

import React, { useState } from 'react';
import { AdminShell } from '../components/shell/AdminShell';
import { PageHeader } from '../components/shell/PageHeader';
import {
  StatCard,
  ChartCard,
  Card,
  Badge,
  Button,
  DataTable,
  Column,
  ConfirmDialog,
} from '@moc-healthy/ui';
import { useAuth } from '../context/AuthContext';

interface SampleOrder {
  id: string;
  code: string;
  customer: string;
  channel: string;
  amount: string;
  status: 'COMPLETED' | 'CONFIRMED' | 'SHIPPING';
}

const SAMPLE_ORDERS: SampleOrder[] = [
  { id: '1', code: 'MOC-1049', customer: 'Nguyễn Văn A', channel: 'Website', amount: '125.000đ', status: 'COMPLETED' },
  { id: '2', code: 'MOC-1050', customer: 'Trần Thị B', channel: 'GrabFood', amount: '89.000đ', status: 'SHIPPING' },
  { id: '3', code: 'MOC-1051', customer: 'Lê Hoàng C', channel: 'Website', amount: '210.000đ', status: 'CONFIRMED' },
];

export default function AdminDashboardPage() {
  const { user, hasPermission } = useAuth();
  const [confirmOpen, setConfirmOpen] = useState(false);

  const columns: Column<SampleOrder>[] = [
    { key: 'code', header: 'Mã đơn', render: (row) => <span className="font-mono font-bold text-slate-900">{row.code}</span> },
    { key: 'customer', header: 'Khách hàng' },
    {
      key: 'channel',
      header: 'Kênh bán',
      render: (row) => (
        <Badge variant={row.channel === 'Website' ? 'success' : 'info'} size="sm">
          {row.channel}
        </Badge>
      ),
    },
    { key: 'amount', header: 'Tổng tiền', render: (row) => <span className="font-bold text-slate-800">{row.amount}</span> },
    {
      key: 'status',
      header: 'Trạng thái',
      render: (row) => (
        <Badge
          variant={row.status === 'COMPLETED' ? 'success' : row.status === 'SHIPPING' ? 'info' : 'warning'}
          size="sm"
        >
          {row.status}
        </Badge>
      ),
    },
  ];

  return (
    <AdminShell>
      <PageHeader
        title="Bảng điều khiển Tổng quan"
        subtitle={`Chào mừng ${user?.full_name || 'Quản trị viên'} — Hệ thống Thương mại & Marketing Tự động hóa Mộc Healthy`}
        breadcrumbs={[{ label: 'Tổng quan' }]}
        actions={
          hasPermission('campaign.create') ? (
            <Button variant="primary" size="sm" onClick={() => setConfirmOpen(true)}>
              + Tạo chiến dịch AI
            </Button>
          ) : undefined
        }
      />

      {/* Top Metric Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          title="Gross Revenue"
          value="128.500.000đ"
          change="14.2%"
          changeType="positive"
          period="So với cùng kỳ tháng trước"
          icon="💰"
        />
        <StatCard
          title="Đơn hàng Đa kênh"
          value="842 đơn"
          change="8.5%"
          changeType="positive"
          period="Website (62%) • Grab (38%)"
          icon="📦"
        />
        <StatCard
          title="Tồn kho theo Lô (Batch)"
          value="10 SKU"
          change="2 Lô HSD < 48h"
          changeType="negative"
          period="Cần ưu tiên đẩy khuyến mãi"
          icon="🥑"
        />
        <StatCard
          title="Chiến dịch AI Marketing"
          value="4 Đang chạy"
          change="2 Chờ duyệt"
          changeType="neutral"
          period="Human-in-the-loop review"
          icon="✨"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Chart Card */}
        <div className="lg:col-span-2">
          <ChartCard
            title="Hiệu quả Doanh thu & Kênh bán hàng"
            subtitle="Phân tách Gross Revenue, Phí nền tảng và Doanh thu thực nhận"
            action={
              <div className="flex gap-1.5">
                <Badge variant="success" size="sm">Website (Net 100%)</Badge>
                <Badge variant="info" size="sm">Grab (Trừ fee)</Badge>
              </div>
            }
          >
            <div className="h-64 flex flex-col items-center justify-center bg-slate-50/70 rounded-xl border border-dashed border-slate-200 text-slate-500">
              <span className="text-3xl mb-2">📊</span>
              <p className="text-sm font-semibold text-slate-700">Khung biểu đồ phân tích ECharts</p>
              <p className="text-xs text-slate-400">Sẽ liên kết dữ liệu thực tế tại Prompt 14 & 25</p>
            </div>
          </ChartCard>
        </div>

        {/* User Profile & RBAC Summary */}
        <div>
          <Card title="Quyền hạn Phiên đăng nhập" className="h-full flex flex-col">
            <div className="space-y-4 flex-1">
              <div>
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
                  Vai trò của bạn:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {user?.roles?.map((role) => (
                    <Badge key={role} variant="success">
                      {role}
                    </Badge>
                  ))}
                  {user?.is_superuser && <Badge variant="warning">SUPERUSER</Badge>}
                </div>
              </div>

              <div>
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
                  Quyền hạn được cấp ({user?.permissions?.length || 0}):
                </span>
                <div className="flex flex-wrap gap-1 max-h-40 overflow-y-auto pr-1">
                  {user?.permissions?.map((perm) => (
                    <span
                      key={perm}
                      className="px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-600 text-[10px] font-mono"
                    >
                      {perm}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Orders Table Shell */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-900">Đơn hàng mới nhất</h2>
          <span className="text-xs text-slate-500">Hiển thị 3 đơn mẫu gần nhất</span>
        </div>
        <DataTable
          columns={columns}
          data={SAMPLE_ORDERS}
          keyExtractor={(row) => row.id}
          currentPage={1}
          totalPages={1}
          onPageChange={() => {}}
        />
      </div>

      <ConfirmDialog
        isOpen={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        onConfirm={() => setConfirmOpen(false)}
        title="Tạo Chiến dịch Marketing AI"
        message="Hệ thống AI sẽ phân tích dữ liệu tồn kho sắp hết hạn và đề xuất chiến dịch kèm nội dung đa nền tảng để bạn phê duyệt."
        confirmText="Bắt đầu tạo"
      />
    </AdminShell>
  );
}
