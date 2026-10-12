'use client';

import React from 'react';
import Link from 'next/link';
import { StorefrontProduct } from '@moc-healthy/contracts';
import { useCart } from '../context/CartContext';

interface ProductCardProps {
  product: StorefrontProduct;
  onAddToCart?: (product: StorefrontProduct) => void;
}

export const ProductCard: React.FC<ProductCardProps> = ({ product, onAddToCart }) => {
  const { addItem, isLoading } = useCart();

  const handleQuickAdd = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (onAddToCart) {
      onAddToCart(product);
    } else {
      await addItem(product.id, 1);
    }
  };
  const formatVnd = (val: number) => {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val);
  };

  const hasDiscount = Boolean(
    product.sale_price && product.sale_price < product.base_price && product.discount_percent
  );

  const getFallbackEmoji = (name: string, catSlug?: string | null) => {
    const n = name.toLowerCase();
    const c = (catSlug || '').toLowerCase();
    if (c.includes('nuoc-ep') || n.includes('ép')) return '🧃';
    if (c.includes('sinh-to') || n.includes('sinh tố')) return '🥑';
    if (c.includes('sua-chua') || n.includes('sữa chua')) return '🍓';
    if (c.includes('tra-matcha') || n.includes('matcha') || n.includes('trà')) return '🍵';
    if (n.includes('táo')) return '🍎';
    if (n.includes('cam')) return '🍊';
    if (n.includes('xoài')) return '🥭';
    if (n.includes('bưởi')) return '🍈';
    if (n.includes('thanh long')) return '🍇';
    return '🥗';
  };

  return (
    <div className="group bg-white rounded-2xl border border-slate-200/80 hover:border-emerald-300 hover:shadow-lg hover:shadow-emerald-900/5 transition-all duration-200 flex flex-col justify-between overflow-hidden">
      <div>
        {/* Media Thumbnail */}
        <Link
          href={`/products/${product.slug}`}
          className="block relative aspect-4/3 bg-slate-50 overflow-hidden cursor-pointer"
        >
          {product.thumbnail ? (
            <img
              src={product.thumbnail}
              alt={product.name}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              loading="lazy"
            />
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-tr from-emerald-50 to-slate-100 group-hover:scale-105 transition-transform duration-300">
              <span className="text-5xl">{getFallbackEmoji(product.name, product.category_slug)}</span>
            </div>
          )}

          {/* Badges */}
          <div className="absolute top-2.5 left-2.5 flex flex-col gap-1 z-10">
            {hasDiscount && (
              <span className="bg-rose-600 text-white font-extrabold text-[10px] px-2 py-0.5 rounded-full shadow-xs">
                -{product.discount_percent}%
              </span>
            )}
            {product.featured && (
              <span className="bg-amber-500 text-white font-bold text-[10px] px-2 py-0.5 rounded-full shadow-xs">
                ⭐ Bán chạy
              </span>
            )}
          </div>
        </Link>

        {/* Content Info */}
        <div className="p-3.5 sm:p-4 space-y-1.5">
          {product.category_name && (
            <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 block">
              {product.category_name}
            </span>
          )}

          <Link href={`/products/${product.slug}`} className="block">
            <h3 className="font-bold text-slate-800 text-xs sm:text-sm line-clamp-2 hover:text-emerald-700 transition leading-snug">
              {product.name}
            </h3>
          </Link>

          {product.short_description && (
            <p className="text-[11px] text-slate-500 line-clamp-1 leading-relaxed">
              {product.short_description}
            </p>
          )}
        </div>
      </div>

      {/* Pricing & Add to Cart */}
      <div className="p-3.5 sm:p-4 pt-0 flex items-center justify-between border-t border-slate-50 mt-1">
        <div>
          <div className="flex items-baseline space-x-1.5">
            <span className="font-extrabold text-emerald-800 text-sm sm:text-base">
              {formatVnd(product.sale_price || product.base_price)}
            </span>
            <span className="text-[10px] text-slate-400">/{product.unit}</span>
          </div>

          {hasDiscount && (
            <span className="text-[11px] text-slate-400 line-through block">
              {formatVnd(product.base_price)}
            </span>
          )}
        </div>

        <button
          type="button"
          onClick={handleQuickAdd}
          disabled={isLoading}
          className="bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1 shadow-xs disabled:opacity-50"
          title="Thêm vào giỏ"
        >
          <span>+</span>
          <span className="hidden sm:inline">Chọn</span>
        </button>
      </div>
    </div>
  );
};
