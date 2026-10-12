'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { storefrontApi } from '../../lib/api';
import {
  StorefrontProduct,
  StorefrontCategory,
  StorefrontProductListResponse,
} from '@moc-healthy/contracts';
import { ProductCard } from '../../components/ProductCard';

function SearchPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const initialQ = searchParams.get('q') || '';
  const initialCat = searchParams.get('category_slug') || '';
  const initialFeatured = searchParams.get('featured') === 'true';

  const [keyword, setKeyword] = useState(initialQ);
  const [selectedCat, setSelectedCat] = useState(initialCat);
  const [sortBy, setSortBy] = useState('newest');

  const [categories, setCategories] = useState<StorefrontCategory[]>([]);
  const [results, setResults] = useState<StorefrontProductListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setKeyword(searchParams.get('q') || '');
    setSelectedCat(searchParams.get('category_slug') || '');
  }, [searchParams]);

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      try {
        setLoading(true);
        const [catsRes, prodsRes] = await Promise.all([
          storefrontApi.getCategories(),
          storefrontApi.getProducts({
            q: keyword.trim() || undefined,
            category_slug: selectedCat || undefined,
            featured: initialFeatured ? true : undefined,
            sort_by: sortBy,
            page_size: 40,
          }),
        ]);

        if (isMounted) {
          setCategories(catsRes);
          setResults(prodsRes);
          setError(null);
        }
      } catch (err: any) {
        console.error('Search error:', err);
        if (isMounted) setError(err.message || 'Lỗi tìm kiếm sản phẩm');
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadData();
    return () => {
      isMounted = false;
    };
  }, [keyword, selectedCat, sortBy, initialFeatured]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const params = new URLSearchParams();
    if (keyword.trim()) params.set('q', keyword.trim());
    if (selectedCat) params.set('category_slug', selectedCat);
    router.push(`/search?${params.toString()}`);
  };

  const handleQuickTagClick = (tag: string) => {
    setKeyword(tag);
    router.push(`/search?q=${encodeURIComponent(tag)}`);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Search Header */}
      <div className="text-center max-w-2xl mx-auto space-y-3">
        <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
          Tìm Kiếm & Thực Đơn Mộc Healthy
        </h1>
        <p className="text-xs sm:text-sm text-slate-600">
          Khám phá trọn vẹn hơn 50+ món trái cây tươi ngon, nước ép ép chậm, sinh tố và sữa chua mỗi ngày.
        </p>

        {/* Search input form */}
        <form onSubmit={handleSearchSubmit} className="relative max-w-xl mx-auto pt-2">
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="Tìm theo tên trái cây, nước ép, sinh tố..."
            className="w-full pl-11 pr-24 py-3 bg-white border border-slate-300 rounded-2xl text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 shadow-sm"
          />
          <span className="absolute left-4 top-5 text-slate-400 text-sm">🔍</span>
          <button
            type="submit"
            className="absolute right-2 top-3.5 bg-emerald-700 hover:bg-emerald-800 text-white font-bold px-4 py-1.5 rounded-xl text-xs transition"
          >
            Tìm kiếm
          </button>
        </form>

        {/* Quick Suggestion Pills */}
        <div className="flex flex-wrap items-center justify-center gap-1.5 text-xs text-slate-500 pt-1">
          <span>Gợi ý:</span>
          {['Táo New Zealand', 'Cam sành', 'Cần tây', 'Bơ sáp', 'Sữa chua dâu'].map((tag) => (
            <button
              key={tag}
              type="button"
              onClick={() => handleQuickTagClick(tag)}
              className="bg-white hover:bg-emerald-50 border border-slate-200 hover:border-emerald-300 px-2.5 py-0.5 rounded-full text-[11px] font-medium text-slate-700 transition"
            >
              {tag}
            </button>
          ))}
        </div>
      </div>

      {/* Filter & Sort Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row gap-4 items-stretch md:items-center justify-between text-xs">
        {/* Category Pills */}
        <div className="flex items-center space-x-2 overflow-x-auto pb-1 scrollbar-none flex-1">
          <button
            type="button"
            onClick={() => setSelectedCat('')}
            className={`px-3 py-1.5 rounded-xl font-bold whitespace-nowrap transition border ${
              !selectedCat
                ? 'bg-emerald-700 text-white border-emerald-700'
                : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
            }`}
          >
            Tất cả
          </button>
          {categories.map((c) => (
            <button
              key={c.id}
              type="button"
              onClick={() => setSelectedCat(selectedCat === c.slug ? '' : c.slug)}
              className={`px-3 py-1.5 rounded-xl font-bold whitespace-nowrap transition border ${
                selectedCat === c.slug
                  ? 'bg-emerald-700 text-white border-emerald-700'
                  : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
              }`}
            >
              {c.name}
            </button>
          ))}
        </div>

        {/* Sort selector */}
        <div className="flex items-center space-x-2 shrink-0">
          <span className="text-slate-500 font-semibold">Sắp xếp:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="newest">Mới nhất</option>
            <option value="price_asc">Giá tăng dần</option>
            <option value="price_desc">Giá giảm dần</option>
            <option value="name_asc">Tên A-Z</option>
          </select>
        </div>
      </div>

      {/* Results Count */}
      <div className="text-xs text-slate-500 font-medium">
        Tìm thấy <strong>{results?.total || 0}</strong> sản phẩm phù hợp
        {keyword && ` với từ khóa "${keyword}"`}
      </div>

      {/* Products Grid */}
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
      ) : results && results.items.length > 0 ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6">
          {results.items.map((prod) => (
            <ProductCard key={prod.id} product={prod} />
          ))}
        </div>
      ) : (
        <div className="text-center py-16 space-y-3 bg-white rounded-3xl border border-slate-200">
          <span className="text-4xl block">🔍</span>
          <h3 className="font-bold text-slate-800 text-base">Không tìm thấy món bạn yêu cầu</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Hãy thử tìm bằng từ khóa chung hơn như "táo", "cam", "sinh tố" hoặc chọn một danh mục ở trên nhé!
          </p>
          <button
            type="button"
            onClick={() => {
              setKeyword('');
              setSelectedCat('');
            }}
            className="px-4 py-2 bg-emerald-700 text-white rounded-xl text-xs font-bold hover:bg-emerald-800"
          >
            Xem toàn bộ thực đơn
          </button>
        </div>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="p-12 text-center text-xs text-slate-500">Đang tải...</div>}>
      <SearchPageContent />
    </Suspense>
  );
}
