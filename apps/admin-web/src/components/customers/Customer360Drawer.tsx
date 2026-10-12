'use client';

import React, { useState, useEffect } from 'react';
import {
  Drawer,
  Button,
  Badge,
} from '@moc-healthy/ui';
import {
  Customer360Response,
  CustomerSegment,
} from '@moc-healthy/contracts';
import { customersApi } from '../../lib/api';
import { LoyaltyAdjustModal } from './LoyaltyAdjustModal';

export interface Customer360DrawerProps {
  isOpen: boolean;
  onClose: () => void;
  customerId: string | null;
  onCustomerUpdated?: () => void;
}

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
    maximumFractionDigits: 0,
  }).format(amount);
};

const formatDate = (isoString?: string | null) => {
  if (!isoString) return '---';
  try {
    const d = new Date(isoString);
    return d.toLocaleDateString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return isoString;
  }
};

const getSegmentConfig = (seg: string) => {
  switch (seg) {
    case 'VIP':
      return { label: '👑 Khách VIP', variant: 'warning' as const, bg: 'bg-amber-100 text-amber-900 border-amber-300' };
    case 'REPEAT':
      return { label: '🔄 Quay lại (Repeat)', variant: 'success' as const, bg: 'bg-emerald-100 text-emerald-900 border-emerald-300' };
    case 'ACTIVE':
      return { label: '🟢 Đang mua (Active)', variant: 'info' as const, bg: 'bg-sky-100 text-sky-900 border-sky-300' };
    case 'NEW':
      return { label: '✨ Khách mới (New)', variant: 'info' as const, bg: 'bg-blue-100 text-blue-900 border-blue-300' };
    case 'AT_RISK':
      return { label: '⚠️ Nguy cơ rời bỏ', variant: 'danger' as const, bg: 'bg-orange-100 text-orange-900 border-orange-300' };
    case 'DORMANT':
      return { label: '💤 Ngủ đông (Dormant)', variant: 'neutral' as const, bg: 'bg-slate-100 text-slate-800 border-slate-300' };
    case 'HIGH_VALUE':
      return { label: '💎 Đơn giá cao', variant: 'warning' as const, bg: 'bg-purple-100 text-purple-900 border-purple-300' };
    default:
      return { label: seg, variant: 'neutral' as const, bg: 'bg-slate-100 text-slate-800 border-slate-300' };
  }
};

export const Customer360Drawer: React.FC<Customer360DrawerProps> = ({
  isOpen,
  onClose,
  customerId,
  onCustomerUpdated,
}) => {
  const [data, setData] = useState<Customer360Response | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'OVERVIEW' | 'ORDERS' | 'LOYALTY'>('OVERVIEW');
  const [isAdjustModalOpen, setIsAdjustModalOpen] = useState(false);

  const loadData = async () => {
    if (!customerId) return;
    setIsLoading(true);
    try {
      const res = await customersApi.get360(customerId);
      setData(res);
    } catch (err) {
      console.error('Không thể tải Customer 360:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && customerId) {
      loadData();
      setActiveTab('OVERVIEW');
    }
  }, [isOpen, customerId]);

  if (!isOpen) return null;

  const segCfg = data ? getSegmentConfig(data.segment) : null;

  return (
    <>
      <Drawer
        isOpen={isOpen}
        onClose={onClose}
        maxWidth="xl"
        title="👥 Hồ Sơ Khách Hàng 360° (Customer 360)"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="outline" size="sm" onClick={onClose}>
              Đóng
            </Button>
          </div>
        }
      >
        {isLoading || !data ? (
          <div className="py-16 text-center text-slate-400 text-sm">
            Đang tải hồ sơ 360 độ khách hàng...
          </div>
        ) : (
          <div className="space-y-5 text-xs text-slate-700">
            {/* 1. Header Profile Banner */}
            <div className="p-4 bg-gradient-to-r from-emerald-50 via-teal-50 to-slate-50 border border-emerald-200/80 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-emerald-700 text-white font-extrabold text-lg flex items-center justify-center shrink-0 shadow-sm">
                  {data.full_name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-bold text-slate-900">{data.full_name}</h3>
                    {segCfg && (
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${segCfg.bg}`}>
                        {segCfg.label}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-slate-500 mt-1">
                    <a href={`tel:${data.phone}`} className="font-mono text-emerald-700 font-semibold hover:underline">
                      📞 {data.phone}
                    </a>
                    {data.email && <span>✉️ {data.email}</span>}
                  </div>
                </div>
              </div>

              {/* Loyalty points pill */}
              <div className="flex items-center gap-2 bg-white px-3 py-2 rounded-xl border border-amber-200 shadow-2xs self-start sm:self-auto">
                <div>
                  <p className="text-[10px] text-slate-400 uppercase font-semibold">Điểm Mộc Xu</p>
                  <p className="text-base font-extrabold text-amber-800 font-mono">
                    {data.loyalty_points.toLocaleString('vi-VN')} <span className="text-[11px]">Xu</span>
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="text-[11px] h-7 px-2 border-amber-300 text-amber-900 hover:bg-amber-50"
                  onClick={() => setIsAdjustModalOpen(true)}
                >
                  ⚡ Đổi điểm
                </Button>
              </div>
            </div>

            {/* 2. Navigation Tabs */}
            <div className="flex border-b border-slate-200">
              <button
                type="button"
                className={`px-3 py-2 text-xs font-semibold border-b-2 transition-colors ${
                  activeTab === 'OVERVIEW'
                    ? 'border-emerald-600 text-emerald-700'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
                onClick={() => setActiveTab('OVERVIEW')}
              >
                📊 Tổng quan & Thói quen
              </button>
              <button
                type="button"
                className={`px-3 py-2 text-xs font-semibold border-b-2 transition-colors ${
                  activeTab === 'ORDERS'
                    ? 'border-emerald-600 text-emerald-700'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
                onClick={() => setActiveTab('ORDERS')}
              >
                📦 Lịch sử đơn hàng ({data.recent_orders.length})
              </button>
              <button
                type="button"
                className={`px-3 py-2 text-xs font-semibold border-b-2 transition-colors ${
                  activeTab === 'LOYALTY'
                    ? 'border-emerald-600 text-emerald-700'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
                onClick={() => setActiveTab('LOYALTY')}
              >
                🪙 Sổ cái Mộc Xu ({data.recent_loyalty_transactions.length})
              </button>
            </div>

            {/* TAB 1: OVERVIEW */}
            {activeTab === 'OVERVIEW' && (
              <div className="space-y-4">
                {/* 4 Financial Stat Cards */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                  <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200">
                    <p className="text-slate-400 text-[10px]">Tổng chi tiêu</p>
                    <p className="font-extrabold text-slate-900 text-sm mt-0.5">
                      {formatCurrency(data.total_spent)}
                    </p>
                  </div>
                  <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200">
                    <p className="text-slate-400 text-[10px]">Số lượng đơn</p>
                    <p className="font-extrabold text-slate-900 text-sm mt-0.5 font-mono">
                      {data.order_count} đơn
                    </p>
                  </div>
                  <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200">
                    <p className="text-slate-400 text-[10px]">Đơn trung bình (AOV)</p>
                    <p className="font-extrabold text-slate-900 text-sm mt-0.5">
                      {formatCurrency(data.average_order_value)}
                    </p>
                  </div>
                  <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200">
                    <p className="text-slate-400 text-[10px]">Lần mua gần nhất</p>
                    <p className="font-bold text-slate-800 text-xs mt-0.5">
                      {data.days_since_last_order !== null
                        ? `${data.days_since_last_order} ngày trước`
                        : 'Chưa có'}
                    </p>
                  </div>
                </div>

                {/* Top Favorite Products */}
                <div className="p-3.5 bg-white border border-slate-200 rounded-xl space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="font-bold text-slate-800 text-xs flex items-center gap-1.5">
                      🥗 Món yêu thích đặt nhiều nhất
                    </h4>
                    <span className="text-[11px] text-slate-400">
                      Kênh hay dùng: <strong className="text-slate-700">{data.most_used_channel}</strong>
                    </span>
                  </div>

                  {data.favorite_products.length === 0 ? (
                    <p className="text-slate-400 text-[11px] py-2">
                      Chưa có dữ liệu lịch sử đặt món để tính toán sở thích.
                    </p>
                  ) : (
                    <div className="divide-y divide-slate-100">
                      {data.favorite_products.map((p, idx) => (
                        <div key={idx} className="py-2 flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="w-5 h-5 rounded-full bg-slate-100 text-slate-600 font-bold text-[10px] flex items-center justify-center">
                              {idx + 1}
                            </span>
                            <span className="font-medium text-slate-800">{p.product_name}</span>
                          </div>
                          <div className="text-right">
                            <span className="font-semibold text-slate-900">{p.quantity_bought} phần</span>
                            <span className="text-slate-400 ml-2">({formatCurrency(p.total_spent)})</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Contact & Tags */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="p-3 bg-white border border-slate-200 rounded-xl space-y-2">
                    <h4 className="font-bold text-slate-800 text-xs">📍 Thông tin giao hàng</h4>
                    <p className="text-slate-600">
                      {data.default_address || 'Chưa lưu địa chỉ mặc định'}
                    </p>
                    <div className="pt-1 text-[11px] text-slate-400 flex items-center gap-3">
                      <span>Nguồn: <strong>{data.source}</strong></span>
                      <span>
                        Marketing SMS: {data.consent_marketing ? '✅ Đồng ý' : '❌ Từ chối'}
                      </span>
                    </div>
                  </div>

                  <div className="p-3 bg-white border border-slate-200 rounded-xl space-y-2">
                    <h4 className="font-bold text-slate-800 text-xs">🏷️ Nhãn phân khúc (Tags)</h4>
                    <div className="flex flex-wrap gap-1.5">
                      {data.tags && data.tags.length > 0 ? (
                        data.tags.map((tag, i) => (
                          <span
                            key={i}
                            className="inline-block px-2 py-0.5 bg-slate-100 text-slate-700 rounded-md text-[11px] font-medium"
                          >
                            #{tag}
                          </span>
                        ))
                      ) : (
                        <span className="text-slate-400 text-[11px]">Chưa gắn nhãn</span>
                      )}
                    </div>
                    {data.notes && (
                      <div className="pt-2 border-t border-slate-100 text-[11px]">
                        <span className="text-slate-400 font-medium">Ghi chú: </span>
                        <span className="text-slate-700">{data.notes}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: ORDERS */}
            {activeTab === 'ORDERS' && (
              <div className="space-y-3">
                {data.recent_orders.length === 0 ? (
                  <div className="py-12 text-center text-slate-400">
                    Khách hàng chưa có đơn hàng nào trong hệ thống.
                  </div>
                ) : (
                  <div className="overflow-x-auto border border-slate-200 rounded-xl">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                        <tr>
                          <th className="py-2 px-3">Mã đơn hàng</th>
                          <th className="py-2 px-3">Ngày đặt</th>
                          <th className="py-2 px-3">Kênh</th>
                          <th className="py-2 px-3 text-right">Tổng tiền</th>
                          <th className="py-2 px-3 text-center">Trạng thái</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {data.recent_orders.map((o) => (
                          <tr key={o.id} className="hover:bg-slate-50/70">
                            <td className="py-2 px-3 font-mono font-bold text-slate-800">
                              #{o.order_number}
                            </td>
                            <td className="py-2 px-3 text-slate-500 whitespace-nowrap">
                              {formatDate(o.created_at)}
                            </td>
                            <td className="py-2 px-3 text-slate-600">{o.source}</td>
                            <td className="py-2 px-3 text-right font-bold text-emerald-800">
                              {formatCurrency(o.total_amount)}
                            </td>
                            <td className="py-2 px-3 text-center">
                              <Badge variant={o.status === 'COMPLETED' ? 'success' : 'info'} size="sm">
                                {o.status}
                              </Badge>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* TAB 3: LOYALTY LEDGER */}
            {activeTab === 'LOYALTY' && (
              <div className="space-y-3">
                <div className="flex items-center justify-between bg-amber-50/60 p-3 rounded-xl border border-amber-200">
                  <div>
                    <span className="text-xs text-amber-900 font-medium">Số dư khả dụng:</span>
                    <p className="text-base font-extrabold text-amber-950 font-mono">
                      {data.loyalty_points.toLocaleString('vi-VN')} Mộc Xu
                    </p>
                  </div>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => setIsAdjustModalOpen(true)}
                  >
                    + Điều chỉnh điểm
                  </Button>
                </div>

                {data.recent_loyalty_transactions.length === 0 ? (
                  <div className="py-8 text-center text-slate-400">
                    Chưa có lịch sử biến động điểm nào.
                  </div>
                ) : (
                  <div className="overflow-x-auto border border-slate-200 rounded-xl">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                        <tr>
                          <th className="py-2 px-3">Thời gian</th>
                          <th className="py-2 px-3">Loại</th>
                          <th className="py-2 px-3 text-right">Biến động</th>
                          <th className="py-2 px-3 text-right">Số dư sau</th>
                          <th className="py-2 px-3">Lý do</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {data.recent_loyalty_transactions.map((tx) => (
                          <tr key={tx.id} className="hover:bg-slate-50/70">
                            <td className="py-2 px-3 text-slate-500 whitespace-nowrap">
                              {formatDate(tx.created_at)}
                            </td>
                            <td className="py-2 px-3">
                              <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-bold ${
                                tx.transaction_type === 'EARN'
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : tx.transaction_type === 'REDEEM'
                                  ? 'bg-rose-100 text-rose-800'
                                  : 'bg-amber-100 text-amber-800'
                              }`}>
                                {tx.transaction_type}
                              </span>
                            </td>
                            <td className={`py-2 px-3 text-right font-bold ${
                              tx.points >= 0 ? 'text-emerald-700' : 'text-rose-600'
                            }`}>
                              {tx.points >= 0 ? `+${tx.points}` : tx.points}
                            </td>
                            <td className="py-2 px-3 text-right font-mono font-medium text-slate-800">
                              {tx.balance_after}
                            </td>
                            <td className="py-2 px-3 text-slate-700">{tx.reason}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </Drawer>

      {/* Adjust Points Modal */}
      {data && (
        <LoyaltyAdjustModal
          isOpen={isAdjustModalOpen}
          onClose={() => setIsAdjustModalOpen(false)}
          customerId={data.id}
          customerName={data.full_name}
          currentPoints={data.loyalty_points}
          onSuccess={() => {
            loadData();
            if (onCustomerUpdated) onCustomerUpdated();
          }}
        />
      )}
    </>
  );
};
