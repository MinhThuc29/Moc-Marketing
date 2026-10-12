'use client';

import React, { useState } from 'react';
import { StorefrontPromotionItem } from '@moc-healthy/contracts';

interface PromoBannerCarouselProps {
  promotions: StorefrontPromotionItem[];
}

export const PromoBannerCarousel: React.FC<PromoBannerCarouselProps> = ({ promotions }) => {
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const handleCopy = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  if (!promotions || promotions.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-extrabold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
          <span>🔥</span> Ưu Đãi & Voucher Đang Áp Dụng
        </h2>
        {copiedCode && (
          <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md animate-in fade-in">
            ✅ Đã chép mã {copiedCode}
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
        {promotions.slice(0, 3).map((promo) => {
          const isFreeship = promo.type === 'FREE_SHIPPING';
          const isFlash = promo.type === 'FLASH_SALE';

          return (
            <div
              key={promo.id}
              className={`p-4 rounded-2xl border transition-all relative overflow-hidden flex flex-col justify-between ${
                isFlash
                  ? 'bg-gradient-to-br from-rose-50 to-orange-50/50 border-rose-200'
                  : isFreeship
                  ? 'bg-gradient-to-br from-emerald-50 to-teal-50/50 border-emerald-200'
                  : 'bg-gradient-to-br from-purple-50 to-indigo-50/50 border-purple-200'
              }`}
            >
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span
                    className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full ${
                      isFlash
                        ? 'bg-rose-600 text-white'
                        : isFreeship
                        ? 'bg-emerald-700 text-white'
                        : 'bg-purple-700 text-white'
                    }`}
                  >
                    {isFlash ? '⚡ Flash Sale' : isFreeship ? '🚚 Miễn Phí Ship' : '🎁 Voucher Mộc'}
                  </span>

                  {promo.code && (
                    <span className="font-mono text-xs font-bold text-slate-700 bg-white/80 px-2 py-0.5 rounded border border-slate-200/80">
                      {promo.code}
                    </span>
                  )}
                </div>

                <h3 className="font-bold text-slate-900 text-xs sm:text-sm line-clamp-1">
                  {promo.title}
                </h3>

                {promo.description && (
                  <p className="text-[11px] text-slate-600 line-clamp-2 leading-relaxed">
                    {promo.description}
                  </p>
                )}
              </div>

              <div className="pt-3 mt-2 border-t border-slate-200/50 flex items-center justify-between text-xs">
                <span className="text-[10px] text-slate-500">
                  {promo.min_order_value
                    ? `Đơn từ ${(promo.min_order_value / 1000).toLocaleString('vi-VN')}k`
                    : 'Mọi đơn hàng'}
                </span>

                {promo.code ? (
                  <button
                    type="button"
                    onClick={() => handleCopy(promo.code!)}
                    className="font-bold text-[11px] text-emerald-700 hover:text-emerald-800 hover:underline cursor-pointer bg-white px-2.5 py-1 rounded-lg border border-emerald-200 shadow-2xs"
                  >
                    {copiedCode === promo.code ? '✓ Đã chép' : 'Sao chép mã'}
                  </button>
                ) : (
                  <span className="text-[11px] text-emerald-700 font-semibold italic">
                    Tự động áp dụng
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
