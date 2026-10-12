'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { storefrontApi } from '../lib/api';
import { StorefrontHomeResponse } from '@moc-healthy/contracts';
import { ProductCard } from '../components/ProductCard';
import { CategoryPillList } from '../components/CategoryPillList';
import { PromoBannerCarousel } from '../components/PromoBannerCarousel';
import { ReviewsSection } from '../components/ReviewsSection';
import { HealthyTipsSection } from '../components/HealthyTipsSection';

export default function StorefrontHomePage() {
  const [data, setData] = useState<StorefrontHomeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function fetchHome() {
      try {
        setLoading(true);
        const res = await storefrontApi.getHome();
        if (isMounted) {
          setData(res);
          setError(null);
        }
      } catch (err: any) {
        console.error('Fetch home error:', err);
        if (isMounted) {
          setError(err.message || 'Không thể tải dữ liệu trang chủ');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    fetchHome();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="space-y-12 pb-12">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-b from-emerald-100/70 via-emerald-50/40 to-transparent pt-8 sm:pt-14 pb-12 px-4 sm:px-6 lg:px-8 overflow-hidden">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          <div className="lg:col-span-7 space-y-5 text-center lg:text-left">
            <div className="inline-flex items-center space-x-2 bg-emerald-600/10 text-emerald-800 border border-emerald-600/20 px-3 py-1 rounded-full text-xs font-bold">
              <span>🥑</span>
              <span>Tươi mới chuẩn sạch — Giao nhanh trong 30 phút</span>
            </div>

            <h1 className="text-3xl sm:text-5xl lg:text-6xl font-black text-slate-900 tracking-tight leading-tight">
              Năng Lượng Xanh Từ{' '}
              <span className="text-emerald-700 underline decoration-emerald-400 decoration-wavy decoration-2">
                Trái Cây Nguyên Bản
              </span>
            </h1>

            <p className="text-sm sm:text-base text-slate-600 max-w-xl mx-auto lg:mx-0 leading-relaxed">
              Mộc Healthy mang đến trái cây loại 1 cắt sẵn tiện dụng, nước ép ép chậm 100% nguyên chất,
              sinh tố bơ béo mịn và sữa chua men sống cho bữa ăn nhẹ lành mạnh mỗi ngày.
            </p>

            <div className="flex flex-wrap items-center justify-center lg:justify-start gap-3 pt-2">
              <Link
                href="/search"
                className="bg-emerald-700 hover:bg-emerald-800 text-white font-extrabold px-6 py-3 rounded-2xl text-xs sm:text-sm shadow-md shadow-emerald-800/20 active:scale-95 transition"
              >
                🥑 Xem Thực Đơn Đầy Đủ
              </Link>
              <Link
                href="/promotions"
                className="bg-white hover:bg-slate-50 text-emerald-800 font-extrabold px-5 py-3 rounded-2xl text-xs sm:text-sm border border-emerald-200 shadow-2xs transition"
              >
                🏷️ Săn Mã Giảm Giá
              </Link>
            </div>

            {/* Quick Metrics */}
            <div className="pt-4 grid grid-cols-3 gap-2 sm:gap-4 max-w-md mx-auto lg:mx-0 text-slate-700">
              <div className="bg-white/80 border border-emerald-100 rounded-xl p-2.5 text-center">
                <span className="text-base sm:text-lg font-black text-emerald-800 block">30 Phút</span>
                <span className="text-[10px] text-slate-500 font-medium">Giao hàng tận nơi</span>
              </div>
              <div className="bg-white/80 border border-emerald-100 rounded-xl p-2.5 text-center">
                <span className="text-base sm:text-lg font-black text-emerald-800 block">100%</span>
                <span className="text-[10px] text-slate-500 font-medium">Không đường hóa học</span>
              </div>
              <div className="bg-white/80 border border-emerald-100 rounded-xl p-2.5 text-center">
                <span className="text-base sm:text-lg font-black text-emerald-800 block">4.9/5 ⭐</span>
                <span className="text-[10px] text-slate-500 font-medium">Hài lòng tuyệt đối</span>
              </div>
            </div>
          </div>

          {/* Hero Visual Card */}
          <div className="lg:col-span-5 flex justify-center">
            <div className="relative w-full max-w-sm aspect-square bg-gradient-to-tr from-emerald-600 to-teal-400 rounded-3xl p-6 shadow-2xl shadow-emerald-800/20 flex flex-col justify-between text-white overflow-hidden">
              <div className="space-y-1">
                <span className="bg-white/20 backdrop-blur-md px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider">
                  Menu Nổi Bật Hôm Nay
                </span>
                <h3 className="text-2xl font-black">Combo Bừng Sức Sống</h3>
                <p className="text-xs text-emerald-100">
                  Táo New Zealand giòn xốp + Nước ép cam sành tươi 100%
                </p>
              </div>

              <div className="flex items-center justify-center py-6 text-7xl select-none">
                🍎 🧃 🥑
              </div>

              <div className="bg-white/10 backdrop-blur-md p-3.5 rounded-2xl flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-emerald-100 block">Chỉ từ</span>
                  <span className="text-xl font-black">69.000₫</span>
                </div>
                <Link
                  href="/search?q=táo"
                  className="bg-white text-emerald-900 font-bold px-3 py-1.5 rounded-xl text-xs hover:bg-emerald-50 transition"
                >
                  Đặt ngay
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        {/* Active Promos & Vouchers Ticker */}
        {data && data.banners && data.banners.length > 0 && (
          <PromoBannerCarousel promotions={data.banners} />
        )}

        {/* Category Pills Bar */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base sm:text-lg font-black text-slate-900 tracking-tight flex items-center gap-2">
              <span>🥑</span> Khám Phá Danh Mục Mộc Healthy
            </h2>
            <Link
              href="/search"
              className="text-xs font-bold text-emerald-700 hover:underline"
            >
              Xem tất cả →
            </Link>
          </div>

          <CategoryPillList categories={data?.categories || []} />
        </section>

        {/* Featured Products / Bán chạy */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-emerald-700 font-extrabold text-xs uppercase tracking-wider block">
                ⭐️ Đề Xuất Cho Bạn
              </span>
              <h2 className="text-lg sm:text-xl font-bold text-slate-900 tracking-tight">
                Sản Phẩm Bán Chạy Nhất Tuần
              </h2>
            </div>
            <Link
              href="/search?featured=true"
              className="text-xs font-bold text-emerald-700 hover:underline"
            >
              Xem thêm →
            </Link>
          </div>

          {loading ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-64 bg-slate-100 rounded-2xl animate-pulse" />
              ))}
            </div>
          ) : error ? (
            <div className="p-8 bg-red-50 text-red-700 text-xs rounded-2xl border border-red-200 text-center">
              {error}
            </div>
          ) : data?.featured_products && data.featured_products.length > 0 ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6">
              {data.featured_products.map((prod) => (
                <ProductCard key={prod.id} product={prod} />
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-xs text-slate-400">
              Đang cập nhật sản phẩm nổi bật...
            </div>
          )}
        </section>

        {/* Category Sections (Trái cây, Nước ép, Sữa chua...) */}
        {data?.category_sections &&
          Object.entries(data.category_sections).map(([slug, prods]) => {
            const cat = data.categories.find((c) => c.slug === slug);
            return (
              <section key={slug} className="space-y-4 pt-2">
                <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                  <div>
                    <h2 className="text-lg sm:text-xl font-extrabold text-slate-900 tracking-tight">
                      {cat ? cat.name : slug}
                    </h2>
                    {cat?.description && (
                      <p className="text-xs text-slate-500 mt-0.5">{cat.description}</p>
                    )}
                  </div>
                  <Link
                    href={`/categories/${slug}`}
                    className="text-xs font-bold text-emerald-700 hover:underline shrink-0"
                  >
                    Xem tất cả ({prods.length}) →
                  </Link>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6">
                  {prods.slice(0, 4).map((p) => (
                    <ProductCard key={p.id} product={p} />
                  ))}
                </div>
              </section>
            );
          })}

        {/* Customer Reviews Section */}
        <ReviewsSection />

        {/* Nutrition & Healthy Tips Section */}
        <HealthyTipsSection />

        {/* Big CTA Banner */}
        <section className="bg-gradient-to-r from-emerald-700 to-teal-700 rounded-3xl p-8 sm:p-12 text-white text-center space-y-4 shadow-xl shadow-emerald-800/10">
          <span className="bg-white/20 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider inline-block">
            ⚡ Giao Nhanh Tận Bàn Làm Việc
          </span>
          <h2 className="text-2xl sm:text-4xl font-black tracking-tight">
            Nạp Năng Lượng Tươi Mới Ngay Hôm Nay
          </h2>
          <p className="text-xs sm:text-sm text-emerald-100 max-w-xl mx-auto leading-relaxed">
            Đặt hàng trực tuyến dễ dàng hoặc liên hệ hotline để được phục vụ trái cây tươi ngon, mát lành nhất!
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Link
              href="/search"
              className="bg-white text-emerald-900 font-extrabold px-6 py-3 rounded-2xl text-xs sm:text-sm hover:bg-emerald-50 transition shadow-sm"
            >
              🛒 Đặt Hàng Ngay
            </Link>
            <a
              href="tel:0901234567"
              className="bg-emerald-800/80 hover:bg-emerald-800 text-white font-bold px-6 py-3 rounded-2xl text-xs sm:text-sm border border-emerald-600 transition"
            >
              📞 Gọi 0901 234 567
            </a>
          </div>
        </section>
      </div>
    </div>
  );
}
