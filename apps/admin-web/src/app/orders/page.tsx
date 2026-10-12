'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Button,
  Input,
  Select,
  Badge,
  DataTable,
  Column,
  EmptyState,
  ErrorState,
  StatCard,
} from '@moc-healthy/ui';
import {
  AdminOrderListItem,
  OrderOverviewStats,
  OrderStatus,
  PaymentStatus,
  OmnichannelPnLResponse,
} from '@moc-healthy/contracts';
import { AdminShell } from '../../components/shell/AdminShell';
import { PageHeader } from '../../components/shell/PageHeader';
import { useAuth } from '../../context/AuthContext';
import { ordersApi, omnichannelApi } from '../../lib/api';
import { OrderDetailDrawer } from '../../components/orders/OrderDetailDrawer';
import { ManualOrderModal } from '../../components/orders/ManualOrderModal';
import { MarketplaceImportModal } from '../../components/orders/MarketplaceImportModal';
import { SettlementReconcileModal } from '../../components/orders/SettlementReconcileModal';

const STATUS_CONFIG: Record<
  OrderStatus,
  { label: string; variant: 'neutral' | 'success' | 'warning' | 'danger' | 'info' }
> = {
  NEW: { label: 'Chờ duyệt', variant: 'warning' },
  CONFIRMED: { label: 'Đã xác nhận', variant: 'info' },
  PREPARING: { label: 'Đang làm', variant: 'warning' },
  READY: { label: 'Sẵn sàng', variant: 'info' },
  SHIPPING: { label: 'Đang giao', variant: 'info' },
  COMPLETED: { label: 'Hoàn thành', variant: 'success' },
  CANCELLED: { label: 'Đã hủy', variant: 'danger' },
  REFUNDED: { label: 'Hoàn tiền', variant: 'neutral' },
};

const PAYMENT_CONFIG: Record<
  PaymentStatus,
  { label: string; variant: 'neutral' | 'success' | 'warning' | 'danger' | 'info' }
> = {
  PENDING: { label: 'Chờ TT', variant: 'warning' },
  PAID: { label: 'Đã TT', variant: 'success' },
  FAILED: { label: 'Thất bại', variant: 'danger' },
  REFUNDED: { label: 'Đã hoàn tiền', variant: 'neutral' },
};

const SOURCE_LABELS: Record<string, string> = {
  ONLINE: 'Website',
  PHONE: 'Hotline',
  WALK_IN: 'Tại quầy',
  ZALO: 'Zalo',
  FACEBOOK: 'FB',
  GRAB: 'GrabFood',
  SHOPEEFOOD: 'ShopeeFood',
  MANUAL: 'Sàn / POS',
};

const formatVND = (amount: number) => {
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
    maximumFractionDigits: 0,
  }).format(amount);
};

export default function OrdersPage() {
  const { hasPermission } = useAuth();
  const canWrite = hasPermission('order.write');

  // Stats
  const [stats, setStats] = useState<OrderOverviewStats | null>(null);

  // Orders list state
  const [orders, setOrders] = useState<AdminOrderListItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  // Filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [selectedPaymentStatus, setSelectedPaymentStatus] = useState<string>('');
  const [selectedSource, setSelectedSource] = useState<string>('');

  // UI state
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Drawer & Modal state
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [isManualModalOpen, setIsManualModalOpen] = useState(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [isSettlementModalOpen, setIsSettlementModalOpen] = useState(false);

  // Omnichannel P&L state
  const [showOmnichannelPnL, setShowOmnichannelPnL] = useState(false);
  const [pnlData, setPnlData] = useState<OmnichannelPnLResponse | null>(null);
  const [isLoadingPnl, setIsLoadingPnl] = useState(false);

  // Load stats
  const loadStats = useCallback(async () => {
    try {
      const data = await ordersApi.getOverview();
      setStats(data);
    } catch (err) {
      console.error('Không thể tải thống kê đơn hàng:', err);
    }
  }, []);

  // Load orders
  const loadOrders = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const res = await ordersApi.list({
        status: selectedStatus || undefined,
        payment_status: selectedPaymentStatus || undefined,
        source: selectedSource || undefined,
        q: searchTerm.trim() || undefined,
        page: currentPage,
        page_size: pageSize,
      });
      setOrders(res.items);
      setTotalCount(res.total);
      setTotalPages(res.total_pages);
    } catch (err: any) {
      setErrorMessage(err.message || 'Không thể tải danh sách đơn hàng');
    } finally {
      setIsLoading(false);
    }
  }, [selectedStatus, selectedPaymentStatus, selectedSource, searchTerm, currentPage]);

  // Load P&L
  const loadPnl = useCallback(async () => {
    setIsLoadingPnl(true);
    try {
      const data = await omnichannelApi.getChannelPnL();
      setPnlData(data);
    } catch (err) {
      console.error('Không thể tải báo cáo P&L kênh:', err);
    } finally {
      setIsLoadingPnl(false);
    }
  }, []);

  useEffect(() => {
    loadStats();
    loadPnl();
  }, [loadStats, loadPnl]);

  useEffect(() => {
    loadOrders();
  }, [loadOrders]);

  const handleOpenDetail = (orderId: string) => {
    setSelectedOrderId(orderId);
    setIsDetailOpen(true);
  };

  const handleRefresh = () => {
    loadStats();
    loadOrders();
    loadPnl();
  };

  const handleClearFilters = () => {
    setSearchTerm('');
    setSelectedStatus('');
    setSelectedPaymentStatus('');
    setSelectedSource('');
    setCurrentPage(1);
  };

  // Status pills filter tab options
  const statusTabs = [
    { key: '', label: 'Tất cả' },
    { key: 'NEW', label: 'Chờ duyệt' },
    { key: 'CONFIRMED', label: 'Đã xác nhận' },
    { key: 'PREPARING', label: 'Đang làm' },
    { key: 'READY', label: 'Sẵn sàng' },
    { key: 'SHIPPING', label: 'Đang giao' },
    { key: 'COMPLETED', label: 'Hoàn thành' },
    { key: 'CANCELLED', label: 'Đã hủy' },
  ];

  const columns: Column<AdminOrderListItem>[] = [
    {
      key: 'order_number',
      header: 'Mã đơn & Ngày đặt',
      render: (item: AdminOrderListItem) => (
        <div className="space-y-0.5">
          <span className="font-bold text-slate-900 block hover:text-emerald-700">
            #{item.order_number}
          </span>
          <span className="text-[11px] text-slate-400 block">
            {new Date(item.created_at).toLocaleString('vi-VN')}
          </span>
          <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold ${
            item.source === 'GRAB'
              ? 'bg-emerald-100 text-emerald-800'
              : item.source === 'SHOPEEFOOD'
              ? 'bg-orange-100 text-orange-800'
              : 'bg-slate-100 text-slate-700'
          }`}>
            {SOURCE_LABELS[item.source] || item.source}
          </span>
        </div>
      ),
    },
    {
      key: 'customer',
      header: 'Khách hàng',
      render: (item: AdminOrderListItem) => (
        <div className="space-y-0.5">
          <span className="font-semibold text-slate-800 block text-xs">
            {item.customer_name}
          </span>
          <a
            href={`tel:${item.customer_phone}`}
            className="text-[11px] text-emerald-700 hover:underline font-mono block"
            onClick={(e) => e.stopPropagation()}
          >
            📞 {item.customer_phone}
          </a>
        </div>
      ),
    },
    {
      key: 'details',
      header: 'Chi tiết & Giao hàng',
      render: (item: AdminOrderListItem) => (
        <div className="max-w-xs space-y-0.5">
          <span className="text-xs text-slate-700 font-medium block">
            📦 {item.items_count} sản phẩm
          </span>
          <span
            className="text-[11px] text-slate-500 block truncate"
            title={item.delivery_address}
          >
            📍 {item.delivery_address}
          </span>
        </div>
      ),
    },
    {
      key: 'total',
      header: 'Tổng tiền & PTTT',
      render: (item: AdminOrderListItem) => (
        <div className="space-y-0.5">
          <span className="font-bold text-emerald-800 text-xs block">
            {formatVND(item.total_amount)}
          </span>
          <span className="text-[11px] text-slate-400 block">
            {item.payment_method === 'COD' ? 'Tiền mặt COD' : 'Chuyển khoản (VietQR)'}
          </span>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Trạng thái đơn',
      render: (item: AdminOrderListItem) => {
        const cfg = STATUS_CONFIG[item.status] || {
          label: item.status,
          variant: 'neutral' as const,
        };
        return (
          <Badge variant={cfg.variant} size="sm">
            {cfg.label}
          </Badge>
        );
      },
    },
    {
      key: 'payment_status',
      header: 'Thanh toán',
      render: (item: AdminOrderListItem) => {
        const cfg = PAYMENT_CONFIG[item.payment_status] || {
          label: item.payment_status,
          variant: 'neutral' as const,
        };
        return (
          <Badge variant={cfg.variant} size="sm">
            {cfg.label}
          </Badge>
        );
      },
    },
    {
      key: 'actions',
      header: 'Thao tác',
      render: (item: AdminOrderListItem) => (
        <Button
          variant="outline"
          size="sm"
          className="text-xs"
          onClick={() => handleOpenDetail(item.id)}
        >
          Xem chi tiết
        </Button>
      ),
    },
  ];

  return (
    <AdminShell requiredPermission="order.read">
      <PageHeader
        title="Quản lý Đơn hàng & Đa kênh (Omnichannel Hub)"
        subtitle="Xử lý đơn hàng tập trung: Website, GrabFood, ShopeeFood, Hotline và POS tại quầy"
        breadcrumbs={[{ label: 'Đơn hàng' }]}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isLoading}>
              🔄 Làm mới
            </Button>
            <Button
              variant={showOmnichannelPnL ? 'secondary' : 'outline'}
              size="sm"
              onClick={() => {
                setShowOmnichannelPnL(!showOmnichannelPnL);
                if (!pnlData) loadPnl();
              }}
            >
              📊 {showOmnichannelPnL ? 'Ẩn P&L sàn ▲' : 'Báo cáo P&L sàn ▼'}
            </Button>
            {canWrite && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsSettlementModalOpen(true)}
                >
                  ⚖️ Đối soát sàn
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsImportModalOpen(true)}
                >
                  📥 Nhập đơn sàn (Grab/Shopee)
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => setIsManualModalOpen(true)}
                >
                  + Tạo đơn thủ công
                </Button>
              </>
            )}
          </div>
        }
      />

      {/* 1. Overview Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          title="Tổng đơn hàng"
          value={stats ? stats.total_orders.toLocaleString('vi-VN') : '—'}
          period="Tất cả các kênh ghi nhận"
          icon="📦"
        />
        <StatCard
          title="Đơn mới chờ duyệt"
          value={stats ? stats.new_orders.toLocaleString('vi-VN') : '—'}
          period={
            stats && stats.new_orders > 0
              ? '⚠️ Cần xác nhận ngay'
              : 'Đã xử lý sạch hàng đợi'
          }
          icon="🔔"
        />
        <StatCard
          title="Đang làm & Đi giao"
          value={stats ? stats.in_progress_orders.toLocaleString('vi-VN') : '—'}
          period="Đang trong quy trình phục vụ"
          icon="🛵"
        />
        <StatCard
          title="Doanh thu hôm nay"
          value={stats ? formatVND(stats.revenue_today) : '—'}
          period={
            stats
              ? `${stats.completed_today} đơn thành công hôm nay`
              : 'Đơn hoàn thành hôm nay'
          }
          icon="💰"
        />
      </div>

      {/* 2. Omnichannel P&L Analysis Section (Collapsible) */}
      {showOmnichannelPnL && (
        <div className="mb-6 bg-gradient-to-br from-slate-900 to-slate-800 text-white rounded-2xl p-5 shadow-lg border border-slate-700 space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-700/80 pb-3">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xl">📊</span>
                <h3 className="text-base font-bold text-white tracking-wide">
                  Phân tích P&L Đa Kênh: Gross Sales vs Chiết Khấu Sàn vs Thực Nhận (Net)
                </h3>
              </div>
              <p className="text-xs text-slate-300 mt-1">
                Phân biệt rõ ràng giữa Doanh số gộp, Chiết khấu hoa hồng sàn (Grab ~20%, ShopeeFood ~25%), Khuyến mãi quán và Doanh thu thực nhận.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                className="bg-slate-800 text-slate-200 border-slate-600 hover:bg-slate-700 text-xs"
                onClick={loadPnl}
                disabled={isLoadingPnl}
              >
                🔄 Cập nhật P&L
              </Button>
            </div>
          </div>

          {isLoadingPnl ? (
            <div className="py-8 text-center text-slate-300 text-xs">
              Đang tổng hợp dữ liệu P&L tài chính...
            </div>
          ) : pnlData ? (
            <>
              {/* Highlight summary cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-slate-900">
                <div className="bg-white/95 rounded-xl p-3 border border-slate-100 shadow-xs">
                  <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Doanh thu gộp (Gross)</p>
                  <p className="text-base font-bold text-slate-900 mt-0.5">
                    {formatVND(pnlData.totals.gross_revenue)}
                  </p>
                  <p className="text-[10px] text-slate-400 mt-0.5">{pnlData.totals.order_count} đơn tổng</p>
                </div>
                <div className="bg-white/95 rounded-xl p-3 border border-slate-100 shadow-xs">
                  <p className="text-[11px] font-semibold text-rose-600 uppercase tracking-wider">Phí sàn / Commission</p>
                  <p className="text-base font-bold text-rose-600 mt-0.5">
                    -{formatVND(pnlData.totals.platform_fees)}
                  </p>
                  <p className="text-[10px] text-slate-400 mt-0.5">Chiết khấu sàn thu</p>
                </div>
                <div className="bg-white/95 rounded-xl p-3 border border-slate-100 shadow-xs">
                  <p className="text-[11px] font-semibold text-emerald-700 uppercase tracking-wider">Thực nhận về quán (Net)</p>
                  <p className="text-base font-bold text-emerald-700 mt-0.5">
                    {formatVND(pnlData.totals.net_settlement)}
                  </p>
                  <p className="text-[10px] text-emerald-600 font-semibold mt-0.5">Tiền về tài khoản</p>
                </div>
                <div className="bg-white/95 rounded-xl p-3 border border-slate-100 shadow-xs">
                  <p className="text-[11px] font-semibold text-sky-700 uppercase tracking-wider">Biên thực nhận (Net Margin)</p>
                  <p className="text-base font-bold text-sky-800 mt-0.5">
                    {pnlData.totals.net_margin_percentage}%
                  </p>
                  <p className="text-[10px] text-slate-400 mt-0.5">AOV: {formatVND(pnlData.totals.average_order_value)}</p>
                </div>
              </div>

              {/* Table breakdown per channel */}
              <div className="overflow-x-auto rounded-xl border border-slate-700">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-800/90 text-slate-200 border-b border-slate-700">
                    <tr>
                      <th className="py-2.5 px-3">Kênh bán hàng</th>
                      <th className="py-2.5 px-3 text-center">Số đơn</th>
                      <th className="py-2.5 px-3 text-right">Doanh thu gộp</th>
                      <th className="py-2.5 px-3 text-right">KM quán chịu</th>
                      <th className="py-2.5 px-3 text-right">Chiết khấu sàn</th>
                      <th className="py-2.5 px-3 text-right">Thực nhận (Net)</th>
                      <th className="py-2.5 px-3 text-right">AOV gộp</th>
                      <th className="py-2.5 px-3 text-right">Biên Net %</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-700/60 bg-slate-800/40 text-slate-200">
                    {pnlData.channels.map((ch) => (
                      <tr key={ch.channel} className="hover:bg-slate-700/50 transition-colors">
                        <td className="py-2 px-3 font-semibold text-white">
                          <span className={`inline-block px-2 py-0.5 rounded text-[11px] mr-2 ${
                            ch.channel === 'GRAB'
                              ? 'bg-emerald-600 text-white'
                              : ch.channel === 'SHOPEEFOOD'
                              ? 'bg-orange-600 text-white'
                              : ch.channel === 'WEBSITE'
                              ? 'bg-blue-600 text-white'
                              : 'bg-slate-600 text-white'
                          }`}>
                            {SOURCE_LABELS[ch.channel] || ch.channel}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-center font-mono font-medium">{ch.order_count}</td>
                        <td className="py-2 px-3 text-right font-medium text-white">{formatVND(ch.gross_revenue)}</td>
                        <td className="py-2 px-3 text-right text-amber-300">-{formatVND(ch.merchant_discount)}</td>
                        <td className="py-2 px-3 text-right text-rose-300 font-medium">-{formatVND(ch.platform_fees)}</td>
                        <td className="py-2 px-3 text-right font-bold text-emerald-400">{formatVND(ch.net_settlement)}</td>
                        <td className="py-2 px-3 text-right text-slate-300">{formatVND(ch.average_order_value)}</td>
                        <td className="py-2 px-3 text-right font-bold text-sky-300">{ch.net_margin_percentage}%</td>
                      </tr>
                    ))}
                    {/* Totals Row */}
                    <tr className="bg-slate-700/70 font-bold text-white border-t-2 border-slate-600">
                      <td className="py-2.5 px-3 uppercase tracking-wider text-xs">Tổng hợp tất cả kênh</td>
                      <td className="py-2.5 px-3 text-center font-mono">{pnlData.totals.order_count}</td>
                      <td className="py-2.5 px-3 text-right text-emerald-200">{formatVND(pnlData.totals.gross_revenue)}</td>
                      <td className="py-2.5 px-3 text-right text-amber-200">-{formatVND(pnlData.totals.merchant_discount)}</td>
                      <td className="py-2.5 px-3 text-right text-rose-200">-{formatVND(pnlData.totals.platform_fees)}</td>
                      <td className="py-2.5 px-3 text-right text-emerald-400">{formatVND(pnlData.totals.net_settlement)}</td>
                      <td className="py-2.5 px-3 text-right text-slate-200">{formatVND(pnlData.totals.average_order_value)}</td>
                      <td className="py-2.5 px-3 text-right text-sky-300">{pnlData.totals.net_margin_percentage}%</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="py-4 text-center text-slate-400 text-xs">
              Chưa có dữ liệu P&L cho khoảng thời gian này.
            </div>
          )}
        </div>
      )}

      {/* 3. Filters & Status Tabs */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-4 shadow-xs mb-6 space-y-4">
        {/* Status Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs border-b border-slate-100">
          <span className="text-slate-400 font-medium mr-2 shrink-0">Trạng thái:</span>
          {statusTabs.map((tab) => {
            const isActive = selectedStatus === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => {
                  setSelectedStatus(tab.key);
                  setCurrentPage(1);
                }}
                className={`px-3 py-1.5 rounded-lg font-medium transition-all shrink-0 ${
                  isActive
                    ? 'bg-emerald-700 text-white shadow-xs'
                    : 'bg-slate-50 text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Detailed Filters row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-12 gap-3 items-end">
          <div className="lg:col-span-5">
            <Input
              label="Tìm kiếm đơn hàng"
              placeholder="Mã đơn (#MOC-xxx), tên khách, số điện thoại..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
            />
          </div>

          <div className="lg:col-span-3">
            <Select
              label="Trạng thái thanh toán"
              value={selectedPaymentStatus}
              onChange={(e) => {
                setSelectedPaymentStatus(e.target.value);
                setCurrentPage(1);
              }}
              options={[
                { value: '', label: 'Tất cả trạng thái TT' },
                { value: 'PAID', label: '✓ Đã thanh toán' },
                { value: 'PENDING', label: '⏳ Chờ thanh toán' },
                { value: 'REFUNDED', label: '↩ Đã hoàn tiền' },
              ]}
            />
          </div>

          <div className="lg:col-span-2">
            <Select
              label="Nguồn đơn / Kênh"
              value={selectedSource}
              onChange={(e) => {
                setSelectedSource(e.target.value);
                setCurrentPage(1);
              }}
              options={[
                { value: '', label: 'Tất cả nguồn' },
                { value: 'ONLINE', label: '🌐 Website Online' },
                { value: 'GRAB', label: '🟢 GrabFood' },
                { value: 'SHOPEEFOOD', label: '🟠 ShopeeFood' },
                { value: 'WALK_IN', label: '🏪 Tại quầy' },
                { value: 'PHONE', label: '📞 Hotline' },
                { value: 'ZALO', label: '💬 Zalo OA' },
                { value: 'FACEBOOK', label: '📘 Facebook' },
                { value: 'MANUAL', label: '📂 Sàn khác / POS' },
              ]}
            />
          </div>

          <div className="lg:col-span-2">
            <Button
              variant="outline"
              size="sm"
              className="w-full h-9"
              onClick={handleClearFilters}
            >
              Xóa bộ lọc
            </Button>
          </div>
        </div>
      </div>

      {/* 4. Orders Table */}
      {errorMessage ? (
        <ErrorState
          title="Không thể tải danh sách đơn hàng"
          message={errorMessage}
          onRetry={loadOrders}
        />
      ) : orders.length === 0 && !isLoading ? (
        <EmptyState
          title="Không tìm thấy đơn hàng nào"
          description={
            searchTerm || selectedStatus || selectedPaymentStatus || selectedSource
              ? 'Thử thay đổi bộ lọc tìm kiếm để xem các đơn hàng khác.'
              : 'Chưa có đơn hàng nào trong hệ thống.'
          }
          icon="🧾"
          actionText={
            searchTerm || selectedStatus || selectedPaymentStatus || selectedSource
              ? 'Xóa bộ lọc'
              : canWrite
              ? '+ Tạo đơn đầu tiên'
              : undefined
          }
          onAction={
            searchTerm || selectedStatus || selectedPaymentStatus || selectedSource
              ? handleClearFilters
              : canWrite
              ? () => setIsManualModalOpen(true)
              : undefined
          }
        />
      ) : (
        <DataTable
          columns={columns}
          data={orders}
          keyExtractor={(item) => item.id}
          isLoading={isLoading}
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={(page) => setCurrentPage(page)}
        />
      )}

      {/* 5. Order Detail Drawer */}
      <OrderDetailDrawer
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
        orderId={selectedOrderId}
        onOrderUpdated={handleRefresh}
      />

      {/* 6. Manual Order Modal */}
      <ManualOrderModal
        isOpen={isManualModalOpen}
        onClose={() => setIsManualModalOpen(false)}
        onOrderCreated={handleRefresh}
      />

      {/* 7. Marketplace Import Modal */}
      <MarketplaceImportModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        onImportSuccess={handleRefresh}
      />

      {/* 8. Settlement Reconcile Modal */}
      <SettlementReconcileModal
        isOpen={isSettlementModalOpen}
        onClose={() => setIsSettlementModalOpen(false)}
        onSettlementUpdated={handleRefresh}
      />
    </AdminShell>
  );
}
