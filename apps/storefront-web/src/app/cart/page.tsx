'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useCart } from '../../context/CartContext';
import { analytics } from '../../lib/analytics';

export default function CartPage() {
  const router = useRouter();
  const {
    cart,
    itemCount,
    isLoading,
    updateQuantity,
    removeItem,
    clearCart,
    applyCoupon,
    removeCoupon,
  } = useCart();

  const [couponCode, setCouponCode] = useState('');
  const [couponLoading, setCouponLoading] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);

  const formatVnd = (val: number) => {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val);
  };

  const handleApplyCoupon = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!couponCode.trim()) return;
    try {
      setCouponLoading(true);
      const res = await applyCoupon(couponCode.trim());
      if (res.success) {
        setCouponCode('');
      }
    } finally {
      setCouponLoading(false);
    }
  };

  const handleProceedToCheckout = () => {
    if (!cart || cart.items.length === 0) return;
    analytics.trackBeginCheckout({
      total: cart.final_total,
      itemCount: cart.total_items,
      items: cart.items,
    });
    router.push('/checkout');
  };

  const freeShipThreshold = 120000;
  const currentSubtotal = cart?.subtotal || 0;
  const amountToFreeShip = Math.max(0, freeShipThreshold - currentSubtotal);
  const freeShipProgress = Math.min(100, Math.round((currentSubtotal / freeShipThreshold) * 100));

  if (!cart || cart.items.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-16 sm:py-24 text-center">
        <div className="bg-white rounded-3xl border border-slate-200/80 p-8 sm:p-12 shadow-xs space-y-5">
          <div className="w-20 h-20 mx-auto rounded-3xl bg-emerald-50 text-emerald-600 flex items-center justify-center text-4xl shadow-inner">
            🛒
          </div>
          <div className="space-y-2">
            <h1 className="text-xl sm:text-2xl font-black text-slate-800">
              Giỏ hàng của bạn đang trống
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 max-w-md mx-auto">
              Chưa có món healthy nào được chọn. Hãy khám phá ngay các loại trái cây tươi ngon cắt sẵn và nước ép nguyên chất nhé!
            </p>
          </div>
          <div className="pt-2">
            <Link
              href="/search"
              className="inline-flex items-center space-x-2 bg-emerald-700 hover:bg-emerald-800 active:scale-95 text-white font-extrabold px-6 py-3.5 rounded-2xl text-xs sm:text-sm transition shadow-md shadow-emerald-700/20"
            >
              <span>🥑</span>
              <span>Khám Phá Thực Đơn Ngay</span>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Title & Clear Cart Header */}
      <div className="flex items-center justify-between border-b border-slate-200/80 pb-4">
        <div className="flex items-center space-x-3">
          <h1 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
            Giỏ Hàng Của Bạn
          </h1>
          <span className="bg-emerald-100 text-emerald-800 text-xs font-extrabold px-2.5 py-0.5 rounded-full">
            {itemCount} món
          </span>
        </div>
        <button
          type="button"
          onClick={() => {
            if (confirm('Bạn có chắc chắn muốn xóa toàn bộ sản phẩm trong giỏ hàng?')) {
              clearCart();
            }
          }}
          className="text-xs font-semibold text-rose-600 hover:text-rose-800 transition"
        >
          Xóa toàn bộ
        </button>
      </div>

      {/* Free Shipping Progress Indicator */}
      <div className="bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200/80 rounded-2xl p-4 space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="font-bold text-emerald-900 flex items-center gap-1.5">
            <span>🚚</span>
            {amountToFreeShip > 0
              ? `Mua thêm ${formatVnd(amountToFreeShip)} để được MIỄN PHÍ VẬN CHUYỂN!`
              : '🎉 Bạn đã đủ điều kiện MIỄN PHÍ VẬN CHUYỂN toàn thành phố!'}
          </span>
          <span className="font-bold text-emerald-700">{freeShipProgress}%</span>
        </div>
        <div className="w-full bg-emerald-200/60 rounded-full h-2 overflow-hidden">
          <div
            className="bg-emerald-600 h-2 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${freeShipProgress}%` }}
          />
        </div>
      </div>

      {/* Warnings if any */}
      {cart.warnings && cart.warnings.length > 0 && (
        <div className="space-y-2">
          {cart.warnings.map((warn, idx) => (
            <div
              key={idx}
              className="p-3 bg-amber-50 border border-amber-200 text-amber-800 text-xs rounded-xl flex items-center space-x-2"
            >
              <span>⚠️</span>
              <span>{warn}</span>
            </div>
          ))}
        </div>
      )}

      {/* Grid Layout: Items & Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Cart Items List */}
        <div className="lg:col-span-8 space-y-4">
          <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs divide-y divide-slate-100 overflow-hidden">
            {cart.items.map((item) => (
              <div key={item.id} className="p-4 sm:p-5 flex items-start gap-4 sm:gap-6">
                {/* Thumbnail */}
                <Link
                  href={`/products/${item.product_slug}`}
                  className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-slate-50 border border-slate-100 overflow-hidden shrink-0 flex items-center justify-center"
                >
                  {item.thumbnail ? (
                    <img
                      src={item.thumbnail}
                      alt={item.product_name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <span className="text-3xl">🥑</span>
                  )}
                </Link>

                {/* Details */}
                <div className="flex-1 min-w-0 space-y-1">
                  <div className="flex items-start justify-between gap-2">
                    <Link
                      href={`/products/${item.product_slug}`}
                      className="font-bold text-slate-900 text-xs sm:text-sm hover:text-emerald-700 transition leading-snug line-clamp-2"
                    >
                      {item.product_name}
                    </Link>
                    <button
                      type="button"
                      onClick={() => removeItem(item.id)}
                      disabled={isLoading}
                      className="text-slate-400 hover:text-rose-600 p-1 text-sm transition"
                      title="Xóa mục này"
                    >
                      ✕
                    </button>
                  </div>

                  <div className="text-[11px] text-slate-400 flex items-center space-x-2">
                    <span>Đơn vị: {item.product_unit}</span>
                    <span>•</span>
                    <span>SKU: {item.product_sku}</span>
                  </div>

                  {item.note && (
                    <div className="text-[11px] text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-md inline-block">
                      Ghi chú: {item.note}
                    </div>
                  )}

                  {/* Pricing & Quantity Controls */}
                  <div className="flex items-center justify-between pt-2">
                    <div className="flex items-baseline space-x-1.5">
                      <span className="font-extrabold text-emerald-800 text-xs sm:text-sm">
                        {formatVnd(item.unit_price)}
                      </span>
                      {item.original_price > item.unit_price && (
                        <span className="text-[11px] text-slate-400 line-through">
                          {formatVnd(item.original_price)}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center border border-slate-200 rounded-xl bg-slate-50/80 overflow-hidden">
                      <button
                        type="button"
                        onClick={() => updateQuantity(item.id, item.quantity - 1, item.note || undefined)}
                        disabled={isLoading}
                        className="px-2.5 py-1 text-slate-600 hover:bg-slate-200 active:bg-slate-300 text-xs font-bold transition"
                      >
                        −
                      </button>
                      <span className="w-8 text-center text-xs font-bold text-slate-900">
                        {item.quantity}
                      </span>
                      <button
                        type="button"
                        onClick={() => updateQuantity(item.id, item.quantity + 1, item.note || undefined)}
                        disabled={isLoading}
                        className="px-2.5 py-1 text-slate-600 hover:bg-slate-200 active:bg-slate-300 text-xs font-bold transition"
                      >
                        +
                      </button>
                    </div>

                    <span className="font-extrabold text-slate-900 text-xs sm:text-sm hidden sm:inline">
                      {formatVnd(item.line_total)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between pt-2">
            <Link
              href="/search"
              className="inline-flex items-center space-x-1 text-xs font-bold text-emerald-700 hover:text-emerald-800 transition"
            >
              <span>←</span>
              <span>Tiếp tục chọn thêm món</span>
            </Link>
          </div>
        </div>

        {/* Right Column: Order Summary & Voucher */}
        <div className="lg:col-span-4 space-y-6">
          {/* Coupon Code Section */}
          <div className="bg-white rounded-3xl border border-slate-200/80 p-5 shadow-xs space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-600">
              Mã Ưu Đãi / Voucher
            </h2>

            {cart.applied_promo_code ? (
              <div className="flex items-center justify-between p-3 bg-emerald-50 border border-emerald-200 rounded-2xl">
                <div className="flex items-center space-x-2 min-w-0">
                  <span className="text-base">🏷️</span>
                  <div className="min-w-0">
                    <span className="font-extrabold text-xs text-emerald-900 block truncate">
                      {cart.applied_promo_code}
                    </span>
                    <span className="text-[10px] text-emerald-700 block truncate">
                      {cart.applied_promo_title || 'Đã áp dụng giảm giá'}
                    </span>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={removeCoupon}
                  disabled={isLoading}
                  className="text-xs font-bold text-rose-600 hover:text-rose-800 ml-2"
                >
                  Gỡ bỏ
                </button>
              </div>
            ) : (
              <form onSubmit={handleApplyCoupon} className="flex gap-2">
                <input
                  type="text"
                  value={couponCode}
                  onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                  placeholder="Nhập mã (WELCOME20, FREESHIP...)"
                  className="flex-1 px-3 py-2.5 rounded-xl border border-slate-200 text-xs uppercase focus:outline-none focus:ring-2 focus:ring-emerald-500 font-bold"
                />
                <button
                  type="submit"
                  disabled={couponLoading || !couponCode.trim()}
                  className="px-4 py-2.5 bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 text-white font-bold rounded-xl text-xs transition"
                >
                  {couponLoading ? '...' : 'Áp dụng'}
                </button>
              </form>
            )}

            {/* Quick voucher suggestions */}
            <div className="pt-1">
              <span className="text-[10px] font-semibold text-slate-400 block mb-1.5">
                Gợi ý mã khuyến mãi:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {['WELCOME20', 'FREESHIP', 'HEALTHY30K'].map((code) => (
                  <button
                    key={code}
                    type="button"
                    onClick={() => applyCoupon(code)}
                    className="text-[10px] bg-slate-100 hover:bg-emerald-50 hover:text-emerald-800 text-slate-700 font-bold px-2 py-1 rounded-lg border border-slate-200 transition"
                  >
                    {code}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Bill Calculation Summary */}
          <div className="bg-white rounded-3xl border border-slate-200/80 p-5 shadow-xs space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-600 border-b border-slate-100 pb-3">
              Tóm Tắt Đơn Hàng
            </h2>

            <div className="space-y-2.5 text-xs text-slate-600">
              <div className="flex justify-between">
                <span>Tạm tính</span>
                <span className="font-bold text-slate-900">{formatVnd(cart.subtotal)}</span>
              </div>

              {cart.discount_amount > 0 && (
                <div className="flex justify-between text-emerald-700">
                  <span>Giảm giá voucher</span>
                  <span className="font-extrabold">-{formatVnd(cart.discount_amount)}</span>
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
                  <span className="font-extrabold">-{formatVnd(cart.shipping_discount)}</span>
                </div>
              )}

              {/* Free gifts if any */}
              {cart.free_gifts && cart.free_gifts.length > 0 && (
                <div className="pt-1 border-t border-slate-100">
                  <span className="text-[11px] font-bold text-emerald-800 block">
                    🎁 Quà tặng kèm:
                  </span>
                  {cart.free_gifts.map((g, i) => (
                    <div key={i} className="text-[11px] text-emerald-700 flex justify-between">
                      <span>• {g.product_name} (x{g.quantity})</span>
                      <span className="font-bold">0₫</span>
                    </div>
                  ))}
                </div>
              )}

              <div className="border-t border-slate-200 pt-3 flex justify-between items-baseline">
                <span className="font-bold text-sm text-slate-900">Tổng thanh toán</span>
                <span className="font-black text-lg sm:text-xl text-emerald-800">
                  {formatVnd(cart.final_total)}
                </span>
              </div>
            </div>

            <div className="pt-2">
              <button
                type="button"
                onClick={handleProceedToCheckout}
                disabled={isLoading}
                className="w-full bg-emerald-700 hover:bg-emerald-800 active:scale-98 text-white font-extrabold py-3.5 px-6 rounded-2xl text-xs sm:text-sm shadow-md shadow-emerald-700/20 transition flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                <span>Tiến Hành Đặt Hàng</span>
                <span>→</span>
              </button>
            </div>

            <div className="text-[11px] text-slate-400 text-center space-y-1 pt-1">
              <p>⚡ Giao nhanh trong 30 phút nội thành</p>
              <p>🌿 100% tươi nguyên chất mỗi ngày</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
