'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useCart } from '../../context/CartContext';
import { checkoutApi } from '../../lib/api';
import { analytics } from '../../lib/analytics';
import { PaymentMethod } from '@moc-healthy/contracts';

export default function CheckoutPage() {
  const router = useRouter();
  const { cart, cartToken, clearCart } = useCart();

  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [customerEmail, setCustomerEmail] = useState('');
  const [deliveryAddress, setDeliveryAddress] = useState('');
  const [customerNote, setCustomerNote] = useState('');
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('COD');
  const [termsAccepted, setTermsAccepted] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [idempotencyKey, setIdempotencyKey] = useState<string>('');

  // Generate unique idempotency key on component mount to prevent duplicate submission
  useEffect(() => {
    setIdempotencyKey(`idem_${Math.random().toString(36).substring(2, 12)}_${Date.now()}`);
  }, []);

  const formatVnd = (val: number) => {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val);
  };

  const handleSubmitOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!cart || cart.items.length === 0) {
      setErrorMessage('Giỏ hàng của bạn đang trống.');
      return;
    }

    if (!customerName.trim() || customerName.trim().length < 2) {
      setErrorMessage('Vui lòng nhập họ và tên của bạn.');
      return;
    }

    const cleanPhone = customerPhone.replace(/\D/g, '');
    if (cleanPhone.length < 9 || cleanPhone.length > 12) {
      setErrorMessage('Số điện thoại không hợp lệ. Vui lòng nhập từ 9-11 số.');
      return;
    }

    if (!deliveryAddress.trim() || deliveryAddress.trim().length < 5) {
      setErrorMessage('Vui lòng nhập địa chỉ giao hàng chi tiết (số nhà, tên đường, phường/xã, quận/huyện).');
      return;
    }

    if (!termsAccepted) {
      setErrorMessage('Bạn cần xác nhận đồng ý với chính sách và điều khoản mua hàng của Mộc Healthy.');
      return;
    }

    try {
      setSubmitting(true);
      const result = await checkoutApi.submitOrder({
        cart_token: cartToken,
        customer_name: customerName.trim(),
        customer_phone: customerPhone.trim(),
        customer_email: customerEmail.trim() || undefined,
        delivery_address: deliveryAddress.trim(),
        customer_note: customerNote.trim() || undefined,
        payment_method: paymentMethod,
        terms_accepted: termsAccepted,
        idempotency_key: idempotencyKey,
      });

      // Track purchase event
      analytics.trackPurchase({
        orderNumber: result.order_number,
        total: result.total_amount,
        shipping: result.shipping_fee,
        paymentMethod: result.payment_method,
      });

      // Clear cart
      await clearCart();

      // Navigate to order confirmation
      router.push(`/order-success?order=${result.order_number}`);
    } catch (err: any) {
      console.error('Checkout error:', err);
      setErrorMessage(err.message || 'Đã có lỗi xảy ra trong quá trình đặt hàng. Vui lòng thử lại.');
    } finally {
      setSubmitting(false);
    }
  };

  if (!cart || cart.items.length === 0) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-20 text-center space-y-4">
        <span className="text-5xl block">🛒</span>
        <h1 className="text-xl font-bold text-slate-800">Giỏ hàng của bạn đang trống</h1>
        <p className="text-xs text-slate-500">
          Vui lòng chọn món trước khi tiến hành thanh toán.
        </p>
        <Link
          href="/search"
          className="inline-block px-5 py-2.5 bg-emerald-700 text-white font-bold rounded-2xl text-xs hover:bg-emerald-800 transition"
        >
          Khám phá thực đơn
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Breadcrumb */}
      <nav className="flex items-center space-x-2 text-xs text-slate-500">
        <Link href="/" className="hover:text-emerald-700 transition">
          Trang chủ
        </Link>
        <span>/</span>
        <Link href="/cart" className="hover:text-emerald-700 transition">
          Giỏ hàng
        </Link>
        <span>/</span>
        <span className="text-slate-900 font-bold">Đặt hàng & Thanh toán</span>
      </nav>

      <div className="border-b border-slate-200/80 pb-4">
        <h1 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
          Thông Tin Đặt Hàng & Thanh Toán
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Hoàn tất đơn hàng nhanh chóng trong 1 bước duy nhất
        </p>
      </div>

      {errorMessage && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 text-xs sm:text-sm rounded-2xl flex items-center space-x-3">
          <span className="text-base">❌</span>
          <span className="font-semibold">{errorMessage}</span>
        </div>
      )}

      <form onSubmit={handleSubmitOrder}>
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Customer & Delivery Info & Payment */}
          <div className="lg:col-span-7 space-y-6">
            {/* 1. Customer Information Card */}
            <div className="bg-white rounded-3xl border border-slate-200/80 p-5 sm:p-6 shadow-xs space-y-4">
              <div className="flex items-center space-x-2.5 border-b border-slate-100 pb-3">
                <span className="w-6 h-6 rounded-full bg-emerald-700 text-white text-xs font-black flex items-center justify-center">
                  1
                </span>
                <h2 className="text-sm font-bold text-slate-900">Thông Tin Khách Hàng</h2>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1 sm:col-span-2">
                  <label className="text-xs font-bold text-slate-700">
                    Họ và tên người nhận <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={customerName}
                    onChange={(e) => setCustomerName(e.target.value)}
                    placeholder="Ví dụ: Nguyễn Văn An"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-600 font-medium"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-700">
                    Số điện thoại liên hệ <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="tel"
                    required
                    value={customerPhone}
                    onChange={(e) => setCustomerPhone(e.target.value)}
                    placeholder="Ví dụ: 0901 234 567"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-600 font-medium"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-700">
                    Email nhận hóa đơn (tùy chọn)
                  </label>
                  <input
                    type="email"
                    value={customerEmail}
                    onChange={(e) => setCustomerEmail(e.target.value)}
                    placeholder="an.nguyen@example.com"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-600 font-medium"
                  />
                </div>
              </div>
            </div>

            {/* 2. Delivery Address Card */}
            <div className="bg-white rounded-3xl border border-slate-200/80 p-5 sm:p-6 shadow-xs space-y-4">
              <div className="flex items-center space-x-2.5 border-b border-slate-100 pb-3">
                <span className="w-6 h-6 rounded-full bg-emerald-700 text-white text-xs font-black flex items-center justify-center">
                  2
                </span>
                <h2 className="text-sm font-bold text-slate-900">Địa Chỉ Nhận Hàng</h2>
              </div>

              <div className="space-y-3">
                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-700">
                    Địa chỉ chi tiết (số nhà, tên đường, phường, quận) <span className="text-rose-500">*</span>
                  </label>
                  <textarea
                    required
                    rows={2}
                    value={deliveryAddress}
                    onChange={(e) => setDeliveryAddress(e.target.value)}
                    placeholder="Ví dụ: Căn hộ 12.04 Tòa Park 7, Vinhomes Central Park, 208 Nguyễn Hữu Cảnh, P.22, Bình Thạnh"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-600 font-medium leading-relaxed"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-700">
                    Ghi chú cho tài xế hoặc bếp (tùy chọn)
                  </label>
                  <input
                    type="text"
                    value={customerNote}
                    onChange={(e) => setCustomerNote(e.target.value)}
                    placeholder="Ví dụ: Gọi trước khi đến 5 phút, gửi lễ tân..."
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-600 font-medium"
                  />
                </div>
              </div>
            </div>

            {/* 3. Payment Method Card */}
            <div className="bg-white rounded-3xl border border-slate-200/80 p-5 sm:p-6 shadow-xs space-y-4">
              <div className="flex items-center space-x-2.5 border-b border-slate-100 pb-3">
                <span className="w-6 h-6 rounded-full bg-emerald-700 text-white text-xs font-black flex items-center justify-center">
                  3
                </span>
                <h2 className="text-sm font-bold text-slate-900">Phương Thức Thanh Toán</h2>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {/* Option 1: COD */}
                <label
                  className={`p-4 rounded-2xl border cursor-pointer transition flex items-start space-x-3 ${
                    paymentMethod === 'COD'
                      ? 'border-emerald-600 bg-emerald-50/60 ring-2 ring-emerald-600/20'
                      : 'border-slate-200 hover:border-slate-300 bg-white'
                  }`}
                >
                  <input
                    type="radio"
                    name="payment_method"
                    value="COD"
                    checked={paymentMethod === 'COD'}
                    onChange={() => setPaymentMethod('COD')}
                    className="mt-0.5 text-emerald-700 focus:ring-emerald-500"
                  />
                  <div>
                    <span className="font-bold text-xs sm:text-sm text-slate-900 block">
                      💵 Tiền mặt khi nhận hàng (COD)
                    </span>
                    <span className="text-[11px] text-slate-500 block mt-0.5">
                      Thanh toán trực tiếp cho shipper khi nhận được đồ tươi ngon
                    </span>
                  </div>
                </label>

                {/* Option 2: Bank Transfer QR */}
                <label
                  className={`p-4 rounded-2xl border cursor-pointer transition flex items-start space-x-3 ${
                    paymentMethod === 'BANK_TRANSFER'
                      ? 'border-emerald-600 bg-emerald-50/60 ring-2 ring-emerald-600/20'
                      : 'border-slate-200 hover:border-slate-300 bg-white'
                  }`}
                >
                  <input
                    type="radio"
                    name="payment_method"
                    value="BANK_TRANSFER"
                    checked={paymentMethod === 'BANK_TRANSFER'}
                    onChange={() => setPaymentMethod('BANK_TRANSFER')}
                    className="mt-0.5 text-emerald-700 focus:ring-emerald-500"
                  />
                  <div>
                    <span className="font-bold text-xs sm:text-sm text-slate-900 block">
                      📲 Chuyển khoản QR (VietQR)
                    </span>
                    <span className="text-[11px] text-slate-500 block mt-0.5">
                      Quét mã QR qua app ngân hàng MBBank, tự động điền số tiền và nội dung
                    </span>
                  </div>
                </label>
              </div>
            </div>

            {/* Terms and Consent Checkbox */}
            <div className="bg-slate-50/80 rounded-2xl p-4 border border-slate-200/80">
              <label className="flex items-start space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  required
                  checked={termsAccepted}
                  onChange={(e) => setTermsAccepted(e.target.checked)}
                  className="mt-0.5 text-emerald-700 rounded focus:ring-emerald-500"
                />
                <span className="text-xs text-slate-600 leading-relaxed">
                  Tôi đã đọc và đồng ý với{' '}
                  <span className="text-emerald-700 font-bold underline">
                    chính sách bảo quản & đổi trả đồ tươi
                  </span>{' '}
                  trong vòng 24h và điều khoản phục vụ của Mộc Healthy.
                </span>
              </label>
            </div>
          </div>

          {/* Right Column: Order Summary & Confirmation Button */}
          <div className="lg:col-span-5 space-y-6">
            <div className="bg-white rounded-3xl border border-slate-200/80 p-5 sm:p-6 shadow-xs space-y-5 sticky top-24">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h2 className="text-sm font-bold text-slate-900">Đơn Hàng Của Bạn</h2>
                <Link href="/cart" className="text-xs text-emerald-700 hover:underline font-bold">
                  Sửa giỏ hàng
                </Link>
              </div>

              {/* Items List Snapshot */}
              <div className="space-y-3 max-h-60 overflow-y-auto pr-1">
                {cart.items.map((item) => (
                  <div key={item.id} className="flex items-center justify-between gap-3 text-xs">
                    <div className="flex items-center space-x-2.5 min-w-0">
                      <span className="font-extrabold text-emerald-700 bg-emerald-50 w-5 h-5 rounded-full flex items-center justify-center text-[10px] shrink-0">
                        {item.quantity}×
                      </span>
                      <span className="font-semibold text-slate-800 truncate">
                        {item.product_name}
                      </span>
                    </div>
                    <span className="font-bold text-slate-900 shrink-0">
                      {formatVnd(item.line_total)}
                    </span>
                  </div>
                ))}
              </div>

              {/* Cost Summary Breakdown */}
              <div className="border-t border-slate-100 pt-3 space-y-2 text-xs text-slate-600">
                <div className="flex justify-between">
                  <span>Tạm tính</span>
                  <span className="font-bold text-slate-900">{formatVnd(cart.subtotal)}</span>
                </div>

                {cart.discount_amount > 0 && (
                  <div className="flex justify-between text-emerald-700">
                    <span>Voucher ({cart.applied_promo_code})</span>
                    <span className="font-bold">-{formatVnd(cart.discount_amount)}</span>
                  </div>
                )}

                <div className="flex justify-between">
                  <span>Phí giao hàng</span>
                  <span>
                    {cart.shipping_fee === 0 ? (
                      <span className="text-emerald-700 font-bold">Miễn phí</span>
                    ) : (
                      formatVnd(cart.shipping_fee)
                    )}
                  </span>
                </div>

                {cart.shipping_discount > 0 && (
                  <div className="flex justify-between text-emerald-700">
                    <span>Ưu đãi freeship</span>
                    <span className="font-bold">-{formatVnd(cart.shipping_discount)}</span>
                  </div>
                )}

                <div className="border-t border-slate-200 pt-3 flex justify-between items-baseline">
                  <span className="font-black text-sm text-slate-900">Tổng thanh toán</span>
                  <span className="font-black text-xl text-emerald-800">
                    {formatVnd(cart.final_total)}
                  </span>
                </div>
              </div>

              {/* Submit Button */}
              <div>
                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full bg-emerald-700 hover:bg-emerald-800 active:scale-98 text-white font-extrabold py-4 px-6 rounded-2xl text-xs sm:text-sm shadow-md shadow-emerald-700/20 transition flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  {submitting ? (
                    <span className="flex items-center gap-2">
                      <span className="animate-spin text-base">⏳</span> Đang tạo đơn hàng...
                    </span>
                  ) : (
                    <span>Xác Nhận Đặt Hàng ({formatVnd(cart.final_total)})</span>
                  )}
                </button>
              </div>

              <div className="text-[11px] text-slate-400 text-center space-y-1">
                <p>🔒 Thông tin đặt hàng được bảo mật tuyệt đối</p>
                <p>📞 Hotline hỗ trợ giao hàng: 0901 234 567</p>
              </div>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}
