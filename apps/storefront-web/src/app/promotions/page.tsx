'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { storefrontApi } from '../../lib/api';
import { StorefrontPromotionItem } from '@moc-healthy/contracts';

export default function StorefrontPromotionsPage() {
  const [promotions, setPromotions] = useState<StorefrontPromotionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadPromos() {
      try {
        setLoading(true);
        const data = await storefrontApi.getPromotions();
        if (isMounted) {
          setPromotions(data);
          setError(null);
        }
      } catch (err: any) {
        console.error('Load promos error:', err);
        if (isMounted) setError(err.message || 'Không thể tải danh sách khuyến mãi');
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadPromos();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2500);
  };

  const formatVnd = (val?: number | null) => {
    if (val === undefined || val === null) return '—';
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="text-center max-w-2xl mx-auto space-y-3">
        <span className="text-[10px] font-extrabold uppercase tracking-wider text-emerald-800 bg-emerald-100 px-3 py-1 rounded-full inline-block">
          🎁 Săn Deal Mỗi Ngày
        </span>
        <h1 className="text-2xl sm:text-4xl font-black text-slate-900 tracking-tight">
          Ưu Đãi & Mã Voucher Mộc Healthy
        </h1>
        <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
          Thu thập các mã giảm giá, voucher freeship và ưu đãi chào bạn mới để thưởng thức trái cây tươi ngon với giá tốt nhất!
        </p>
      </div>

      {/* Copied feedback */}
      {copiedCode && (
        <div className="max-w-md mx-auto p-3 bg-emerald-50 border border-emerald-300 text-emerald-800 text-xs font-bold rounded-2xl text-center shadow-xs animate-in fade-in">
          🎉 Đã sao chép mã <strong>{copiedCode}</strong>! Nhập mã tại bước thanh toán để nhận ưu đãi.
        </div>
      )}

      {/* Promotions Cards Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-48 bg-slate-100 rounded-3xl animate-pulse" />
          ))}
        </div>
      ) : error ? (
        <div className="p-12 text-center bg-red-50 text-red-700 text-xs rounded-2xl border border-red-200">
          {error}
        </div>
      ) : promotions.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {promotions.map((promo) => {
            const isFreeship = promo.type === 'FREE_SHIPPING';
            const isFlash = promo.type === 'FLASH_SALE';
            const endDate = new Date(promo.end_at).toLocaleDateString('vi-VN');

            return (
              <div
                key={promo.id}
                className="bg-white rounded-3xl border border-slate-200/90 shadow-xs hover:shadow-md hover:border-emerald-300 transition-all p-5 flex flex-col justify-between space-y-4"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span
                      className={`text-[10px] font-extrabold uppercase px-2.5 py-0.5 rounded-full ${
                        isFlash
                          ? 'bg-rose-100 text-rose-800 border border-rose-200'
                          : isFreeship
                          ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                          : 'bg-purple-100 text-purple-800 border border-purple-200'
                      }`}
                    >
                      {isFlash
                        ? '⚡ Flash Sale'
                        : isFreeship
                        ? '🚚 Miễn Phí Ship'
                        : '🏷️ Mã Voucher'}
                    </span>

                    <span className="text-[10px] text-slate-400 font-medium">HSD: {endDate}</span>
                  </div>

                  <div>
                    <h3 className="font-extrabold text-slate-900 text-base leading-snug">
                      {promo.title}
                    </h3>
                    {promo.description && (
                      <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                        {promo.description}
                      </p>
                    )}
                  </div>

                  {/* Conditions */}
                  <div className="bg-slate-50 p-3 rounded-2xl text-[11px] text-slate-600 space-y-1 border border-slate-100">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Đơn tối thiểu:</span>
                      <strong className="text-slate-800">
                        {promo.min_order_value ? formatVnd(promo.min_order_value) : 'Không yêu cầu'}
                      </strong>
                    </div>

                    {promo.max_discount && (
                      <div className="flex justify-between">
                        <span className="text-slate-400">Mức giảm tối đa:</span>
                        <strong className="text-slate-800">{formatVnd(promo.max_discount)}</strong>
                      </div>
                    )}

                    {promo.stackable && (
                      <div className="flex justify-between text-purple-700 font-semibold">
                        <span>Quy tắc:</span>
                        <span>Được gộp cùng ưu đãi khác</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Bottom Action */}
                <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                  {promo.code ? (
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-xs bg-slate-100 border border-slate-200 px-2 py-1 rounded-xl text-slate-800">
                        {promo.code}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleCopyCode(promo.code!)}
                        className="text-xs font-bold text-emerald-700 hover:text-emerald-800 underline cursor-pointer"
                      >
                        {copiedCode === promo.code ? 'Đã lưu ✓' : 'Lưu mã'}
                      </button>
                    </div>
                  ) : (
                    <span className="text-xs text-emerald-700 font-bold italic">
                      Tự động kích hoạt khi đủ điều kiện
                    </span>
                  )}

                  <Link
                    href="/search"
                    className="bg-emerald-700 hover:bg-emerald-800 text-white font-bold px-3 py-1.5 rounded-xl text-xs transition"
                  >
                    Dùng Ngay →
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-16 space-y-3 bg-white rounded-3xl border border-slate-200">
          <span className="text-4xl block">🏷️</span>
          <h3 className="font-bold text-slate-800 text-base">Hiện chưa có khuyến mãi mới</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Hãy theo dõi thường xuyên để không bỏ lỡ các ưu đãi giờ vàng và mã voucher mới nhất nhé!
          </p>
          <Link
            href="/"
            className="inline-block px-4 py-2 bg-emerald-700 text-white rounded-xl text-xs font-bold hover:bg-emerald-800"
          >
            Về trang chủ
          </Link>
        </div>
      )}
    </div>
  );
}
