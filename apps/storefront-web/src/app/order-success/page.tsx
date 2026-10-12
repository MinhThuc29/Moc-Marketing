'use client';

import React, { Suspense, useState, useEffect } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { checkoutApi } from '../../lib/api';
import { CheckoutResult } from '@moc-healthy/contracts';

function OrderSuccessContent() {
  const searchParams = useSearchParams();
  const orderNumber = searchParams.get('order') || '';

  const [order, setOrder] = useState<CheckoutResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  useEffect(() => {
    if (!orderNumber) {
      setLoading(false);
      setError('Thiếu mã đơn hàng.');
      return;
    }

    async function loadOrder() {
      try {
        setLoading(true);
        const data = await checkoutApi.getOrderByNumber(orderNumber);
        setOrder(data);
      } catch (err: any) {
        console.error('Failed to load order:', err);
        setError(err.message || 'Không thể tải thông tin đơn hàng.');
      } finally {
        setLoading(false);
      }
    }

    loadOrder();
  }, [orderNumber]);

  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2500);
  };

  const formatVnd = (val: number) => {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val);
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-20 text-center space-y-4">
        <div className="w-16 h-16 mx-auto rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center text-3xl animate-bounce">
          🥑
        </div>
        <h2 className="text-lg font-bold text-slate-800">Đang tải thông tin đơn hàng...</h2>
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-20 text-center space-y-4">
        <span className="text-5xl block">⚠️</span>
        <h2 className="text-xl font-bold text-slate-800">Không tìm thấy đơn hàng</h2>
        <p className="text-xs text-slate-500">
          Mã đơn hàng không hợp lệ hoặc đã xảy ra sự cố trong quá trình truy xuất.
        </p>
        <Link
          href="/"
          className="inline-block px-5 py-2.5 bg-emerald-700 text-white font-bold rounded-2xl text-xs hover:bg-emerald-800 transition"
        >
          Về trang chủ
        </Link>
      </div>
    );
  }

  const isBankTransfer = order.payment_method === 'BANK_TRANSFER' && order.bank_transfer_instruction;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 space-y-8">
      {/* Congratulations Card */}
      <div className="bg-gradient-to-tr from-emerald-800 via-emerald-700 to-teal-800 rounded-3xl p-6 sm:p-10 text-white shadow-xl space-y-4 text-center sm:text-left relative overflow-hidden">
        <div className="relative z-10 flex flex-col sm:flex-row items-center gap-6">
          <div className="w-20 h-20 rounded-3xl bg-white/20 backdrop-blur-md flex items-center justify-center text-4xl shrink-0 shadow-inner">
            🎉
          </div>
          <div className="space-y-1.5">
            <span className="bg-emerald-500/40 text-emerald-100 font-extrabold text-[10px] uppercase px-2.5 py-1 rounded-full inline-block">
              Đơn Hàng Mới Được Tiếp Nhận
            </span>
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight">
              Đặt Hàng Thành Công!
            </h1>
            <p className="text-xs sm:text-sm text-emerald-100 leading-relaxed max-w-xl">
              Cảm ơn quý khách <strong className="text-white">{order.customer_name}</strong> đã lựa chọn Mộc Healthy. Đội ngũ bếp đang chuẩn bị những phần trái cây và đồ uống tươi ngon nhất để giao tới bạn!
            </p>
          </div>
        </div>
      </div>

      {/* Order Info & Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
        {/* Card 1: Order Details */}
        <div className="bg-white rounded-3xl border border-slate-200/80 p-5 sm:p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Chi Tiết Đơn Hàng
            </h2>
            <span className="bg-emerald-100 text-emerald-800 font-black text-xs px-2.5 py-0.5 rounded-full">
              Mã: {order.order_number}
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <span className="text-slate-400 block text-[11px]">Người nhận:</span>
              <span className="font-bold text-slate-900">{order.customer_name}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[11px]">Số điện thoại:</span>
              <span className="font-bold text-slate-900">{order.customer_phone}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[11px]">Địa chỉ giao hàng:</span>
              <span className="font-semibold text-slate-800 leading-relaxed block">
                {order.delivery_address}
              </span>
            </div>
            {order.customer_note && (
              <div>
                <span className="text-slate-400 block text-[11px]">Ghi chú đơn hàng:</span>
                <span className="italic text-slate-700">{order.customer_note}</span>
              </div>
            )}
            <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
              <span className="text-slate-500">Phương thức thanh toán:</span>
              <span className="font-bold text-slate-900">
                {order.payment_method === 'COD'
                  ? '💵 Tiền mặt khi nhận hàng'
                  : '📲 Chuyển khoản QR (VietQR)'}
              </span>
            </div>
          </div>
        </div>

        {/* Card 2: Payment Guidance */}
        <div className="bg-white rounded-3xl border border-slate-200/80 p-5 sm:p-6 shadow-xs space-y-4">
          <div className="border-b border-slate-100 pb-3">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Hướng Dẫn Thanh Toán
            </h2>
          </div>

          {isBankTransfer && order.bank_transfer_instruction ? (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row items-center gap-4 bg-emerald-50/50 p-4 rounded-2xl border border-emerald-100">
                {/* VietQR Image */}
                <div className="w-36 h-36 bg-white p-2 rounded-xl border border-slate-200 shadow-xs shrink-0 flex items-center justify-center">
                  <img
                    src={order.bank_transfer_instruction.qr_code_url}
                    alt="VietQR Code"
                    className="w-full h-full object-contain"
                  />
                </div>
                <div className="space-y-1.5 text-xs text-left w-full">
                  <span className="text-[10px] text-emerald-700 font-bold uppercase">
                    Quét mã QR bằng App Ngân Hàng
                  </span>
                  <p className="text-[11px] text-slate-600">
                    Mở app ngân hàng bất kỳ (MBBank, Vietcombank, Techcombank...) quét mã để tự động điền đúng thông tin.
                  </p>
                </div>
              </div>

              {/* Bank Details with Copy */}
              <div className="space-y-2 text-xs bg-slate-50 p-3.5 rounded-2xl border border-slate-100">
                <div className="flex justify-between items-center">
                  <span className="text-slate-500">Ngân hàng:</span>
                  <span className="font-bold text-slate-900">
                    {order.bank_transfer_instruction.bank_name}
                  </span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-slate-500">Số tài khoản:</span>
                  <div className="flex items-center space-x-2">
                    <span className="font-extrabold text-slate-900 tracking-wider">
                      {order.bank_transfer_instruction.account_number}
                    </span>
                    <button
                      type="button"
                      onClick={() =>
                        copyToClipboard(
                          order.bank_transfer_instruction!.account_number,
                          'account'
                        )
                      }
                      className="text-[10px] bg-white border border-slate-200 px-2 py-0.5 rounded font-bold text-emerald-700 hover:bg-emerald-50"
                    >
                      {copiedField === 'account' ? '✓ Đã chép' : 'Sao chép'}
                    </button>
                  </div>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-slate-500">Chủ tài khoản:</span>
                  <span className="font-bold text-slate-900">
                    {order.bank_transfer_instruction.account_holder}
                  </span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-slate-500">Số tiền:</span>
                  <span className="font-black text-emerald-800 text-sm">
                    {formatVnd(order.total_amount)}
                  </span>
                </div>

                <div className="flex justify-between items-center pt-1 border-t border-slate-200">
                  <span className="text-slate-500">Nội dung chuyển khoản:</span>
                  <div className="flex items-center space-x-2">
                    <span className="font-black text-rose-700 tracking-wider">
                      {order.bank_transfer_instruction.transfer_content}
                    </span>
                    <button
                      type="button"
                      onClick={() =>
                        copyToClipboard(
                          order.bank_transfer_instruction!.transfer_content,
                          'content'
                        )
                      }
                      className="text-[10px] bg-white border border-slate-200 px-2 py-0.5 rounded font-bold text-emerald-700 hover:bg-emerald-50"
                    >
                      {copiedField === 'content' ? '✓ Đã chép' : 'Sao chép'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-4 bg-emerald-50/60 rounded-2xl border border-emerald-100 text-xs text-slate-700 space-y-2">
              <div className="flex items-center space-x-2 text-emerald-800 font-bold">
                <span className="text-base">💵</span>
                <span>Thanh toán bằng tiền mặt khi nhận hàng (COD)</span>
              </div>
              <p className="text-[11px] text-slate-600 leading-relaxed">
                Shipper Mộc Healthy sẽ liên hệ trước khi giao. Quý khách vui lòng chuẩn bị số tiền chính xác{' '}
                <strong className="text-slate-900 font-black">{formatVnd(order.total_amount)}</strong>{' '}
                khi nhận hàng.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Ordered Items Recap */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-5 sm:p-6 shadow-xs space-y-4">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 border-b border-slate-100 pb-3">
          Danh Sách Món Trong Đơn Hàng ({order.items.length} món)
        </h2>

        <div className="divide-y divide-slate-100">
          {order.items.map((it) => (
            <div key={it.id} className="py-3 flex items-center justify-between text-xs">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-slate-50 border border-slate-100 overflow-hidden flex items-center justify-center shrink-0">
                  {it.thumbnail ? (
                    <img src={it.thumbnail} alt={it.product_name} className="w-full h-full object-cover" />
                  ) : (
                    <span>🥑</span>
                  )}
                </div>
                <div>
                  <span className="font-bold text-slate-900 block">{it.product_name}</span>
                  <span className="text-[10px] text-slate-400">
                    {formatVnd(it.unit_price)} × {it.quantity} {it.product_unit}
                  </span>
                </div>
              </div>
              <span className="font-extrabold text-slate-900">{formatVnd(it.total_price)}</span>
            </div>
          ))}
        </div>

        {/* Bill calculation recap */}
        <div className="border-t border-slate-100 pt-3 space-y-1.5 text-xs text-slate-600">
          <div className="flex justify-between">
            <span>Tạm tính</span>
            <span className="font-bold text-slate-900">{formatVnd(order.subtotal)}</span>
          </div>
          {order.discount_amount > 0 && (
            <div className="flex justify-between text-emerald-700">
              <span>Giảm giá ({order.applied_promo_code})</span>
              <span className="font-bold">-{formatVnd(order.discount_amount)}</span>
            </div>
          )}
          <div className="flex justify-between">
            <span>Phí vận chuyển</span>
            <span className="font-bold">
              {order.shipping_fee === 0 ? 'Miễn phí' : formatVnd(order.shipping_fee)}
            </span>
          </div>
          <div className="border-t border-slate-200 pt-2 flex justify-between items-baseline">
            <span className="font-black text-sm text-slate-900">Tổng cộng</span>
            <span className="font-black text-lg text-emerald-800">
              {formatVnd(order.total_amount)}
            </span>
          </div>
        </div>
      </div>

      {/* CTA Buttons */}
      <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
        <Link
          href={`/tracking?order=${encodeURIComponent(order.order_number)}&phone=${encodeURIComponent(order.customer_phone)}`}
          className="w-full sm:w-auto px-6 py-3.5 bg-emerald-700 hover:bg-emerald-800 text-white font-extrabold rounded-2xl text-xs sm:text-sm text-center shadow-md shadow-emerald-700/20 transition flex items-center justify-center gap-2"
        >
          <span>🔍</span>
          <span>Theo Dõi Đơn Hàng</span>
        </Link>
        <Link
          href="/"
          className="w-full sm:w-auto px-6 py-3.5 bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold rounded-2xl text-xs sm:text-sm text-center transition"
        >
          Tiếp Tục Mua Sắm
        </Link>
        <a
          href="tel:0901234567"
          className="w-full sm:w-auto px-5 py-3.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-bold rounded-2xl text-xs sm:text-sm text-center transition"
        >
          📞 Hotline: 0901 234 567
        </a>
      </div>
    </div>
  );
}

export default function OrderSuccessPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-3xl mx-auto px-4 py-20 text-center">
          <span className="text-3xl animate-bounce block">🥑</span>
          <p className="text-xs text-slate-500 mt-2">Đang tải...</p>
        </div>
      }
    >
      <OrderSuccessContent />
    </Suspense>
  );
}
