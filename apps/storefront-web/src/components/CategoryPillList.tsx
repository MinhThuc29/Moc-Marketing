'use client';

import React from 'react';
import Link from 'next/link';

interface CategoryPillListProps {
  categories: Array<{
    id: string;
    name: string;
    slug: string;
    product_count?: number;
  }>;
  activeSlug?: string;
}

export const CategoryPillList: React.FC<CategoryPillListProps> = ({ categories, activeSlug }) => {
  return (
    <div className="flex items-center space-x-2 overflow-x-auto pb-2 scrollbar-none text-xs">
      <Link
        href="/search"
        className={`px-4 py-2 rounded-full font-bold whitespace-nowrap transition border ${
          !activeSlug
            ? 'bg-emerald-700 text-white border-emerald-700 shadow-xs'
            : 'bg-white text-slate-700 border-slate-200 hover:border-emerald-300 hover:bg-emerald-50/50'
        }`}
      >
        🌟 Tất Cả Thực Đơn
      </Link>

      {categories.map((cat) => {
        const isActive = activeSlug === cat.slug;
        return (
          <Link
            key={cat.id}
            href={`/categories/${cat.slug}`}
            className={`px-4 py-2 rounded-full font-bold whitespace-nowrap transition border flex items-center gap-1.5 ${
              isActive
                ? 'bg-emerald-700 text-white border-emerald-700 shadow-xs'
                : 'bg-white text-slate-700 border-slate-200 hover:border-emerald-300 hover:bg-emerald-50/50'
            }`}
          >
            <span>{cat.name}</span>
            {cat.product_count !== undefined && cat.product_count > 0 && (
              <span
                className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                  isActive ? 'bg-emerald-800 text-white' : 'bg-slate-100 text-slate-500'
                }`}
              >
                {cat.product_count}
              </span>
            )}
          </Link>
        );
      })}
    </div>
  );
};
