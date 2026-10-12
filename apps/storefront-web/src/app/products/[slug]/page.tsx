'use client';

import React, { useState, useEffect, use } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { storefrontApi } from '../../../lib/api';
import { StorefrontProductDetail } from '@moc-healthy/contracts';
import { ProductCard } from '../../../components/ProductCard';
import { useCart } from '../../../context/CartContext';

interface ProductDetailPageProps {
  params: Promise<{ slug: string }>;
}

export default function ProductDetailPage({ params }: ProductDetailPageProps) {
  const router = useRouter();
  const { addItem, isLoading: cartLoading } = useCart();
  const resolvedParams = use(params);
  const slug = resolvedParams.slug;

  const [product, setProduct] = useState<StorefrontProductDetail | null>(null);
  const [selectedMedia, setSelectedMedia] = useState<string | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [addedNotice, setAddedNotice] = useState(false);

  useEffect(() => {
    let isMounted = true;
    async function loadProduct() {
      try {
        setLoading(true);
        const data = await storefrontApi.getProduct(slug);
        if (isMounted) {
          setProduct(data);
          setSelectedMedia(data.thumbnail || (data.media && data.media[0]) || null);
          setError(null);
        }
      } catch (err: any) {
        console.error('Load product detail error:', err);
        if (isMounted) {
          setError(err.message || 'Không tìm thấy sản phẩm');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadProduct();
    return () => {
      isMounted = false;
    };
  }, [slug]);

  const formatVnd = (val: number) => {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val);
  };

  const handleAddToCart = async () => {
    if (!product) return;
    const ok = await addItem(product.id, quantity);
    if (ok) {
      setAddedNotice(true);
      setTimeout(() => setAddedNotice(false), 2500);
    }
  };

  const handleBuyNow = async () => {
    if (!product) return;
    await addItem(product.id, quantity);
    router.push('/checkout');
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 animate-pulse">
          <div className="aspect-square bg-slate-200 rounded-3xl" />
          <div className="space-y-4">
            <div className="h-6 w-32 bg-slate-200 rounded" />
            <div className="h-10 w-3/4 bg-slate-200 rounded" />
            <div className="h-8 w-1/3 bg-slate-200 rounded" />
            <div className="h-24 w-full bg-slate-200 rounded" />
            <div className="h-12 w-48 bg-slate-200 rounded" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-20 text-center space-y-4">
        <span className="text-5xl block">🥑</span>
        <h2 className="text-xl font-bold text-slate-800">Không tìm thấy sản phẩm</h2>
        <p className="text-xs text-slate-500">
          Sản phẩm bạn đang tìm kiếm không tồn tại hoặc đã tạm dừng kinh doanh.
        </p>
        <Link
          href="/search"
          className="inline-block px-5 py-2.5 bg-emerald-700 text-white font-bold rounded-2xl text-xs hover:bg-emerald-800 transition"
        >
          Khám phá thực đơn khác
        </Link>
      </div>
    );
  }

  const hasDiscount = Boolean(
    product.sale_price && product.sale_price < product.base_price && product.discount_percent
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-12">
      {/* Breadcrumb */}
      <nav className="flex items-center space-x-2 text-xs text-slate-500">
        <Link href="/" className="hover:text-emerald-700 transition">
          Trang chủ
        </Link>
        <span>/</span>
        {product.category_slug && (
          <>
            <Link
              href={`/categories/${product.category_slug}`}
              className="hover:text-emerald-700 transition"
            >
              {product.category_name || product.category_slug}
            </Link>
            <span>/</span>
          </>
        )}
        <span className="text-slate-900 font-bold truncate max-w-xs">{product.name}</span>
      </nav>

      {/* Main Product Info */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-8 lg:gap-12 items-start">
        {/* Left Column: Media Gallery */}
        <div className="md:col-span-6 space-y-4">
          <div className="aspect-square bg-white rounded-3xl border border-slate-200 overflow-hidden relative shadow-sm flex items-center justify-center">
            {selectedMedia ? (
              <img
                src={selectedMedia}
                alt={product.name}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="flex flex-col items-center justify-center p-8 text-center text-7xl">
                🥑
              </div>
            )}

            {hasDiscount && (
              <span className="absolute top-4 left-4 bg-rose-600 text-white font-black text-xs px-3 py-1 rounded-full shadow-md">
                GIẢM {product.discount_percent}%
              </span>
            )}
          </div>

          {/* Media Thumbnails if more than 1 */}
          {product.media && product.media.length > 1 && (
            <div className="flex gap-2 overflow-x-auto pb-2">
              {product.media.map((url, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setSelectedMedia(url)}
                  className={`w-16 h-16 rounded-xl border-2 overflow-hidden shrink-0 transition ${
                    selectedMedia === url
                      ? 'border-emerald-600 ring-2 ring-emerald-500/20'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <img src={url} alt={`Thumbnail ${idx}`} className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Information & Actions */}
        <div className="md:col-span-6 space-y-6">
          <div className="space-y-2 border-b border-slate-100 pb-5">
            <div className="flex items-center space-x-2">
              {product.category_name && (
                <Link
                  href={`/categories/${product.category_slug}`}
                  className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full hover:bg-emerald-100 transition"
                >
                  {product.category_name}
                </Link>
              )}
              <span className="text-[11px] text-slate-400 font-mono">SKU: {product.sku}</span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight leading-tight">
              {product.name}
            </h1>

            {product.short_description && (
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                {product.short_description}
              </p>
            )}
          </div>

          {/* Price Block */}
          <div className="bg-slate-50/80 p-4 rounded-2xl border border-slate-200/80 flex items-center justify-between">
            <div>
              <div className="flex items-baseline space-x-3">
                <span className="text-2xl sm:text-3xl font-black text-emerald-800">
                  {formatVnd(product.sale_price || product.base_price)}
                </span>
                <span className="text-xs text-slate-500">/{product.unit}</span>
              </div>

              {hasDiscount && (
                <div className="flex items-center space-x-2 text-xs mt-0.5">
                  <span className="text-slate-400 line-through">
                    {formatVnd(product.base_price)}
                  </span>
                  <span className="text-rose-600 font-bold">
                    Tiết kiệm {formatVnd(product.base_price - (product.sale_price || 0))}
                  </span>
                </div>
              )}
            </div>

            <span className="text-emerald-700 bg-emerald-100/80 text-[11px] font-bold px-2.5 py-1 rounded-xl">
              🟢 Còn hàng tươi mới
            </span>
          </div>

          {/* Quantity Selector & Add to Cart */}
          <div className="space-y-3 pt-2">
            <div className="flex items-center space-x-4">
              <span className="text-xs font-bold text-slate-700">Số lượng:</span>
              <div className="flex items-center border border-slate-200 rounded-xl bg-white overflow-hidden shadow-2xs">
                <button
                  type="button"
                  onClick={() => setQuantity(Math.max(1, quantity - 1))}
                  className="px-3 py-1.5 text-slate-600 hover:bg-slate-50 text-sm font-bold"
                >
                  −
                </button>
                <input
                  type="number"
                  min="1"
                  value={quantity}
                  onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value, 10) || 1))}
                  className="w-12 text-center text-xs font-bold text-slate-800 focus:outline-none"
                />
                <button
                  type="button"
                  onClick={() => setQuantity(quantity + 1)}
                  className="px-3 py-1.5 text-slate-600 hover:bg-slate-50 text-sm font-bold"
                >
                  +
                </button>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <button
                type="button"
                onClick={handleAddToCart}
                className="flex-1 bg-emerald-700 hover:bg-emerald-800 active:scale-98 text-white font-extrabold py-3.5 px-6 rounded-2xl text-xs sm:text-sm shadow-md shadow-emerald-800/20 transition flex items-center justify-center gap-2 cursor-pointer"
              >
                <span>🛒</span> Thêm Vào Giỏ Hàng
              </button>
              <button
                type="button"
                onClick={handleBuyNow}
                className="bg-emerald-100 hover:bg-emerald-200 text-emerald-900 font-extrabold py-3.5 px-6 rounded-2xl text-xs sm:text-sm transition flex items-center justify-center gap-2 cursor-pointer"
              >
                ⚡ Mua Ngay
              </button>
            </div>

            {addedNotice && (
              <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold rounded-xl text-center animate-in fade-in">
                ✅ Đã thêm {quantity} {product.unit} "{product.name}" vào giỏ hàng!
              </div>
            )}
          </div>

          {/* Nutritional & Quality Specifications */}
          <div className="border-t border-slate-100 pt-6 space-y-4 text-xs">
            <h3 className="font-extrabold text-slate-900 uppercase tracking-wider text-[11px]">
              🥗 Thông Tin Dinh Dưỡng & Bảo Quản
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-slate-600">
              {product.ingredients && (
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                  <span className="font-bold text-slate-800 block mb-0.5">Thành phần:</span>
                  <span>{product.ingredients}</span>
                </div>
              )}

              {product.nutrition_text && (
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                  <span className="font-bold text-slate-800 block mb-0.5">Dinh dưỡng:</span>
                  <span>{product.nutrition_text}</span>
                </div>
              )}

              {product.shelf_life && (
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                  <span className="font-bold text-slate-800 block mb-0.5">Hạn sử dụng:</span>
                  <span>{product.shelf_life}</span>
                </div>
              )}

              {product.storage_note && (
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                  <span className="font-bold text-slate-800 block mb-0.5">Bảo quản:</span>
                  <span>{product.storage_note}</span>
                </div>
              )}
            </div>

            {product.description && (
              <div className="pt-2">
                <span className="font-bold text-slate-800 block mb-1">Mô tả sản phẩm:</span>
                <p className="text-slate-600 leading-relaxed whitespace-pre-line">
                  {product.description}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Related Products Section */}
      {product.related_products && product.related_products.length > 0 && (
        <section className="space-y-4 pt-8 border-t border-slate-100">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-emerald-700 font-extrabold text-xs uppercase tracking-wider block">
                Gợi ý cùng danh mục
              </span>
              <h2 className="text-lg sm:text-xl font-bold text-slate-900 tracking-tight">
                Món Ngon Kèm Theo Bạn Có Thể Thích
              </h2>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6">
            {product.related_products.map((rel) => (
              <ProductCard key={rel.id} product={rel} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
