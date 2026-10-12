'use client';

import React, { Suspense, useState, useEffect } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { trackingApi } from '../../lib/api';
import { OrderTrackingResponse, OrderStatus } from '@moc-healthy/contracts';

const STEPPER_STEPS = [
  { key: 'NEW', label: 'Tiếp Nhận', icon: '📝', description: 'Đã nhận đơn trên hệ thống' },
  { key: 'CONFIRMED', label: 'Xác Nhận', icon: '📞', description: 'Cửa hàng đã duyệt đơn' },
  { key: 'PREPARING', label: 'Chuẩn Bị', icon: '🥗', description: 'Bếp cắt gọt và đóng hộp' },
  { key: 'SHIPPING', label: 'Đang Giao', icon: '🛵', description: 'Shipper đang trên đường giao' },
  { key: 'COMPLETED', label: 'Hoàn Thành', icon: '🎉', description: 'Giao hàng thành công' },
];

function getStepIndex(status: OrderStatus): number {
  switch (status) {
    case 'NEW':
      return 0;
    case 'CONFIRMED':
      return 1;
    case 'PREPARING':
    case 'READY':
      return 2;
    case 'SHIPPING':
      return 3;
    case 'COMPLETED':
      return 4;
    default:
      return -1;
  }
}

function TrackingContent() {
  const searchParams = useSearchParams();
  const initialOrder = searchParams.get('order') || '';
  const initialPhone = searchParams.get('phone') || '';

  const [orderNumber, setOrderNumber] = useState(initialOrder);
  const [phone, setPhone] = useState(initialPhone);
  const [trackingData, setTrackingData] = useState<OrderTrackingResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTracking = async (searchOrder: string, searchPhone?: string) => {
    if (!searchOrder.trim()) {
      setError('Vui lòng nhập mã đơn hàng.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await trackingApi.trackOrder(
        searchOrder.trim().replace(/^#/, ''),
        searchPhone ? searchPhone.trim() : undefined
      );
      setTrackingData(data);
    } catch (err: any) {
      setTrackingData(null);
      setError(err.message || 'Không tìm thấy đơn hàng phù hợp.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialOrder) {
      fetchTracking(initialOrder, initialPhone);
    }
  }, [initialOrder, initialPhone]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchTracking(orderNumber, phone);
  };

  const formatVnd = (val: number) => {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val);
  };

  const currentStepIdx = trackingData ? getStepIndex(trackingData.status) : -1;
  const isCancelled = trackingData?.status === 'CANCELLED';
  const isRefunded = trackingData?.status === 'REFUNDED';

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 space-y-8">
      {/* Page Header */}
      <div className="text-center space-y-2">
        <span className="inline-block px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 font-extrabold text-[11px] tracking-wide uppercase">
          Tra Cứu Trực Tuyến
        </span>
        <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
          Theo Dõi Trạng Thái Đơn Hàng
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 max-w-xl mx-auto">
          Nhập mã đơn hàng hoặc số điện thoại người nhận để cập nhật tiến độ chế biến và giao hàng thời gian thực.
        </p>
      </div>

      {/* Lookup Form */}
      <form
        onSubmit={handleSearchSubmit}
        className="bg-white p-5 sm:p-6 rounded-3xl border border-slate-200/90 shadow-sm space-y-4 max-w-2xl mx-auto"
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="space-y-1">
            <label className="text-xs font-bold text-slate-700 block">
              Mã đơn hàng *
            </label>
            <input
              type="text"
              required
              placeholder="VD: MOC-261007-ABC1"
              value={orderNumber}
              onChange={(e) => setOrderNumber(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs font-mono uppercase focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-bold text-slate-700 block">
              Số điện thoại người nhận
            </label>
            <input
              type="tel"
              placeholder="VD: 0901234567"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 bg-emerald-700 hover:bg-emerald-800 disabled:opacity-60 text-white font-extrabold rounded-xl text-xs sm:text-sm shadow-md shadow-emerald-700/20 transition flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Đang tra cứu...</span>
            </>
          ) : (
            <>
              <span>🔍</span>
              <span>Tra Cứu Đơn Hàng</span>
            </>
          )}
        </button>

        {error && (
          <div className="p-3 bg-red-50 text-red-700 text-xs rounded-xl border border-red-200 text-center">
            {error}
          </div>
        )}
      </form>

      {/* Tracking Result View */}
      {trackingData && (
        <div className="space-y-8 animate-in fade-in duration-300">
          {/* Status Stepper Banner */}
          <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/90 shadow-sm space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-2">
              <div>
                <span className="text-[11px] font-semibold text-slate-400 block uppercase tracking-wider">
                  Mã Đơn Hàng
                </span>
                <span className="text-xl sm:text-2xl font-black text-slate-900 font-mono">
                  #{trackingData.order_number}
                </span>
              </div>
              <div className="text-left sm:text-right">
                <span className="text-[11px] font-semibold text-slate-400 block">Ngày đặt hàng</span>
                <span className="text-xs font-bold text-slate-700">
                  {new Date(trackingData.created_at).toLocaleString('vi-VN')}
                </span>
              </div>
            </div>

            {/* Stepper / Timeline Visual */}
            {isCancelled || isRefunded ? (
              <div className="p-4 bg-red-50 rounded-2xl border border-red-200 text-center space-y-1">
                <span className="text-2xl block">⚠️</span>
                <h3 className="font-extrabold text-red-800 text-sm">
                  {isCancelled ? 'Đơn hàng đã được hủy' : 'Đơn hàng đã hoàn tiền'}
                </h3>
                <p className="text-xs text-red-600">
                  Nếu bạn cần thêm thông tin, vui lòng liên hệ hotline bộ phận CSKH Mộc Healthy.
                </p>
              </div>
            ) : (
              <div className="py-4">
                <div className="grid grid-cols-5 gap-2 relative">
                  {STEPPER_STEPS.map((step, idx) => {
                    const isDone = currentStepIdx >= idx;
                    const isCurrent = currentStepIdx === idx;

                    return (
                      <div key={step.key} className="flex flex-col items-center text-center relative z-10">
                        <div
                          className={`w-10 h-10 sm:w-12 sm:h-12 rounded-2xl flex items-center justify-center text-base sm:text-lg font-bold transition-all shadow-xs ${
                            isCurrent
                              ? 'bg-emerald-600 text-white ring-4 ring-emerald-100 scale-105'
                              : isDone
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-slate-100 text-slate-400'
                          }`}
                        >
                          {isDone ? step.icon : '•'}
                        </div>
                        <span
                          className={`mt-2 font-black text-[11px] sm:text-xs block ${
                            isCurrent
                              ? 'text-emerald-700'
                              : isDone
                              ? 'text-slate-800'
                              : 'text-slate-400'
                          }`}
                        >
                          {step.label}
                        </span>
                        <span className="text-[10px] text-slate-400 hidden sm:block mt-0.5 leading-tight">
                          {step.description}
                        </span>
                      </div>
                    );
                  })}
                </div>

                {/* Progress bar background */}
                <div className="w-full bg-slate-100 h-1.5 rounded-full -mt-10 sm:-mt-12 mb-10 sm:mb-12 relative z-0">
                  <div
                    className="bg-emerald-500 h-1.5 rounded-full transition-all duration-500"
                    style={{
                      width: `${(Math.max(0, currentStepIdx) / (STEPPER_STEPS.length - 1)) * 100}%`,
                    }}
                  />
                </div>
              </div>
            )}

            {/* Quick Status Pill */}
            <div className="p-3 bg-emerald-50/70 rounded-2xl border border-emerald-100 flex items-center justify-between text-xs">
              <span className="text-emerald-900">
                Phương thức thanh toán: <strong>{trackingData.payment_method === 'COD' ? 'Tiền mặt (COD)' : 'Chuyển khoản VietQR'}</strong>
              </span>
              <span className={`px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider ${
                trackingData.payment_status === 'PAID'
                  ? 'bg-emerald-200 text-emerald-900'
                  : 'bg-amber-100 text-amber-800'
              }`}>
                {trackingData.payment_status === 'PAID' ? '✓ Đã Thanh Toán' : '⏳ Chờ Thanh Toán'}
              </span>
            </div>
          </div>

          {/* Details & Items */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Delivery Details */}
            <div className="bg-white p-6 rounded-3xl border border-slate-200/90 shadow-sm space-y-4 md:col-span-1">
              <h3 className="font-bold text-xs uppercase tracking-wider text-slate-400">
                Thông Tin Giao Nhận
              </h3>
              <div className="space-y-2 text-xs">
                <div>
                  <span className="text-slate-400 block text-[11px]">Người nhận</span>
                  <span className="font-extrabold text-slate-800">{trackingData.customer_name}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[11px]">Địa chỉ nhận hàng</span>
                  <span className="text-slate-700 leading-relaxed block">{trackingData.delivery_address}</span>
                </div>
              </div>

              {/* Support Call */}
              <div className="pt-4 border-t border-slate-100 space-y-2">
                <span className="text-[11px] text-slate-400 block">Cần hỗ trợ về đơn hàng?</span>
                <a
                  href="tel:0901234567"
                  className="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold rounded-xl text-xs flex items-center justify-center gap-1.5 transition"
                >
                  📞 Hotline: 0901 234 567
                </a>
              </div>
            </div>

            {/* Line items list */}
            <div className="bg-white p-6 rounded-3xl border border-slate-200/90 shadow-sm space-y-4 md:col-span-2">
              <h3 className="font-bold text-xs uppercase tracking-wider text-slate-400">
                Sản Phẩm Trong Đơn ({trackingData.items.length} món)
              </h3>

              <div className="divide-y divide-slate-100">
                {trackingData.items.map((it) => (
                  <div key={it.id} className="py-3 flex items-center justify-between gap-3 text-xs">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center text-base shrink-0 font-bold">
                        🥗
                      </div>
                      <div>
                        <p className="font-bold text-slate-800">{it.product_name}</p>
                        <p className="text-[11px] text-slate-400">
                          {formatVnd(it.unit_price)} x {it.quantity} {it.product_unit}
                        </p>
                        {it.note && (
                          <p className="text-[11px] text-emerald-700 italic">Ghi chú: {it.note}</p>
                        )}
                      </div>
                    </div>
                    <span className="font-bold text-slate-900 shrink-0">
                      {formatVnd(it.total_price)}
                    </span>
                  </div>
                ))}
              </div>

              <div className="border-t border-slate-200 pt-3 flex items-baseline justify-between">
                <span className="font-bold text-xs text-slate-700">Tổng thanh toán:</span>
                <span className="font-black text-lg text-emerald-800">
                  {formatVnd(trackingData.total_amount)}
                </span>
              </div>
            </div>
          </div>

          {/* Timeline Audit Trail */}
          {trackingData.status_history && trackingData.status_history.length > 0 && (
            <div className="bg-white p-6 rounded-3xl border border-slate-200/90 shadow-sm space-y-4">
              <h3 className="font-bold text-xs uppercase tracking-wider text-slate-400">
                Lịch Sử Xử Lý Đơn Hàng
              </h3>

              <div className="space-y-4 relative pl-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
                {trackingData.status_history.map((hist) => (
                  <div key={hist.id} className="relative text-xs">
                    <div className="absolute -left-6 top-1 w-2.5 h-2.5 rounded-full bg-emerald-600 ring-4 ring-emerald-100" />
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between">
                      <span className="font-bold text-slate-800">
                        {hist.old_status ? `${hist.old_status} ➔ ` : 'Tiếp nhận đơn: '}
                        <span className="text-emerald-700">{hist.new_status}</span>
                      </span>
                      <span className="text-[11px] text-slate-400 font-mono">
                        {new Date(hist.created_at).toLocaleString('vi-VN')}
                      </span>
                    </div>
                    {hist.reason && (
                      <p className="text-slate-500 text-[11px] mt-0.5 italic">{hist.reason}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Navigation Links */}
      <div className="text-center pt-4">
        <Link
          href="/"
          className="text-xs text-emerald-700 hover:text-emerald-800 font-bold hover:underline"
        >
          ← Quay lại trang chủ mua sắm
        </Link>
      </div>
    </div>
  );
}

export default function OrderTrackingPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-3xl mx-auto px-4 py-20 text-center">
          <span className="text-3xl animate-bounce block">🥑</span>
          <p className="text-xs text-slate-500 mt-2">Đang tải trang tra cứu...</p>
        </div>
      }
    >
      <TrackingContent />
    </Suspense>
  );
}
