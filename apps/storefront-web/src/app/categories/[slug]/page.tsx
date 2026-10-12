'use client';

import React, { useState, useEffect, use } from 'react';
import Link from 'next/link';
import { storefrontApi } from '../../../lib/api';
import {
  StorefrontProduct,
  StorefrontCategory,
  StorefrontProductListResponse,
} from '@moc-healthy/contracts';
import { ProductCard } from '../../../components/ProductCard';
import { CategoryPillList } from '../../../components/CategoryPillList';

interface CategoryPageProps {
  params: Promise<{ slug: string }>;
}

export default function CategoryPage({ params }: CategoryPageProps) {
  const resolvedParams = use(params);
  const slug = resolvedParams.slug;

  const [categories, setCategories] = useState<StorefrontCategory[]>([]);
  const [currentCategory, setCurrentCategory] = useState<StorefrontCategory | null>(null);
  const [productsData, setProductsData] = useState<StorefrontProductListResponse | null>(null);
  const [sortBy, setSortBy] = useState('newest');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadCategoryData() {
      try {
        setLoading(true);
        const [catsRes, prodsRes] = await Promise.all([
          storefrontApi.getCategories(),
          storefrontApi.getProducts({
            category_slug: slug,
            sort_by: sortBy,
            page_size: 30,
          }),
        ]);

        if (isMounted) {
          setCategories(catsRes);
          const current = catsRes.find((c) => c.slug === slug) || null;
          setCurrentCategory(current);
          setProductsData(prodsRes);
          setError(null);
        }
      } catch (err: any) {
        console.error('Load category error:', err);
        if (isMounted) setError(err.message || 'Không thể tải danh mục sản phẩm');
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadCategoryData();
    return () => {
      isMounted = false;
    };
  }, [slug, sortBy]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Breadcrumb */}
      <nav className="flex items-center space-x-2 text-xs text-slate-500">
        <Link href="/" className="hover:text-emerald-700 transition">
          Trang chủ
        </Link>
        <span>/</span>
        <Link href="/search" className="hover:text-emerald-700 transition">
          Thực đơn
        </Link>
        <span>/</span>
        <span className="text-slate-800 font-bold">
          {currentCategory ? currentCategory.name : slug}
        </span>
      </nav>

      {/* Category Header */}
      <div className="bg-gradient-to-r from-emerald-50 via-teal-50/40 to-slate-50 p-6 sm:p-8 rounded-3xl border border-emerald-100 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1.5 max-w-2xl">
          <span className="text-[10px] font-extrabold uppercase tracking-wider text-emerald-700 bg-emerald-100/80 px-2.5 py-0.5 rounded-full inline-block">
            Danh mục thực phẩm lành mạnh
          </span>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            {currentCategory ? currentCategory.name : slug}
          </h1>
          {currentCategory?.description && (
            <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
              {currentCategory.description}
            </p>
          )}
        </div>

        <div className="text-right shrink-0">
          <span className="text-sm font-bold text-slate-700 block">
            {productsData ? `${productsData.total} sản phẩm` : 'Đang tải...'}
          </span>
          <span className="text-[11px] text-emerald-700 font-semibold">Tươi mới mỗi ngày</span>
        </div>
      </div>

      {/* Category Horizontal Pills */}
      <CategoryPillList categories={categories} activeSlug={slug} />

      {/* Filter / Sort bar */}
      <div className="flex items-center justify-between border-b border-slate-200/80 pb-4 text-xs">
        <span className="text-slate-500 font-medium">
          Hiển thị <strong>{productsData?.items.length || 0}</strong> sản phẩm
        </span>

        <div className="flex items-center space-x-2">
          <span className="text-slate-500 font-medium">Sắp xếp:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-3 py-1.5 bg-white border border-slate-200 rounded-xl font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="newest">Mới nhất</option>
            <option value="price_asc">Giá tăng dần</option>
            <option value="price_desc">Giá giảm dần</option>
            <option value="name_asc">Tên A-Z</option>
          </select>
        </div>
      </div>

      {/* Product Grid */}
      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-64 bg-slate-100 rounded-2xl animate-pulse" />
          ))}
        </div>
      ) : error ? (
        <div className="p-12 text-center bg-red-50 text-red-700 text-xs rounded-2xl border border-red-200">
          {error}
        </div>
      ) : productsData && productsData.items.length > 0 ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6">
          {productsData.items.map((prod) => (
            <ProductCard key={prod.id} product={prod} />
          ))}
        </div>
      ) : (
        <div className="text-center py-16 space-y-3 bg-white rounded-3xl border border-slate-200">
          <span className="text-4xl block">🥗</span>
          <h3 className="font-bold text-slate-800 text-base">Chưa có sản phẩm trong danh mục này</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Mộc Healthy đang chuẩn bị các món mới thơm ngon, hãy quay lại sau hoặc khám phá các danh mục khác nhé!
          </p>
          <Link
            href="/search"
            className="inline-block px-4 py-2 bg-emerald-700 text-white rounded-xl text-xs font-bold hover:bg-emerald-800"
          >
            Khám phá thực đơn khác
          </Link>
        </div>
      )}
    </div>
  );
}
