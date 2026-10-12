'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useCart } from '../../context/CartContext';

export const Header: React.FC = () => {
  const router = useRouter();
  const { itemCount } = useCart();
  const [searchQuery, setSearchQuery] = useState('');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
      setIsMobileMenuOpen(false);
    }
  };

  return (
    <>
      {/* Top Announcement Bar */}
      <div className="bg-emerald-800 text-emerald-50 text-[11px] sm:text-xs py-1.5 px-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="bg-emerald-700 text-emerald-200 px-1.5 py-0.5 rounded text-[10px] font-bold uppercase">
              Freeship
            </span>
            <span className="font-medium">
              Miễn phí giao hàng toàn thành phố cho đơn từ 120.000₫ • Giao nhanh trong 30 phút!
            </span>
          </div>
          <div className="hidden sm:flex items-center space-x-4 text-emerald-200 text-[11px]">
            <span>⏰ Mở cửa: 07:00 - 21:30</span>
            <a href="tel:0901234567" className="hover:text-white font-semibold">
              📞 0901 234 567
            </a>
          </div>
        </div>
      </div>

      {/* Main Header */}
      <header className="bg-white/95 backdrop-blur-md border-b border-slate-100 sticky top-0 z-40 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 sm:h-20 flex items-center justify-between gap-4">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-3 shrink-0">
            <div className="w-10 h-10 sm:w-11 sm:h-11 rounded-2xl bg-gradient-to-tr from-emerald-700 to-emerald-500 flex items-center justify-center text-white font-extrabold text-xl shadow-md shadow-emerald-700/20">
              M
            </div>
            <div>
              <span className="text-lg sm:text-xl font-black tracking-tight text-slate-900 block leading-tight">
                Mộc Healthy
              </span>
              <span className="text-[10px] text-emerald-700 font-bold uppercase tracking-wider block">
                Fresh & Clean Food
              </span>
            </div>
          </Link>

          {/* Search Bar (Desktop) */}
          <form
            onSubmit={handleSearchSubmit}
            className="hidden md:flex flex-1 max-w-md mx-4 relative items-center"
          >
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Tìm táo New Zealand, nước ép cam, sinh tố bơ..."
              className="w-full pl-10 pr-20 py-2.5 rounded-full text-xs bg-slate-100/80 border border-slate-200 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-600 transition"
            />
            <span className="absolute left-3.5 text-slate-400 text-sm">🔍</span>
            <button
              type="submit"
              className="absolute right-1.5 px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-full text-xs font-semibold transition"
            >
              Tìm
            </button>
          </form>

          {/* Navigation Links (Desktop) */}
          <nav className="hidden lg:flex items-center space-x-6 text-xs font-semibold text-slate-700">
            <Link href="/" className="hover:text-emerald-700 transition py-1">
              Trang Chủ
            </Link>
            <Link href="/search" className="hover:text-emerald-700 transition py-1">
              Thực Đơn
            </Link>
            <Link href="/promotions" className="hover:text-emerald-700 transition py-1 flex items-center gap-1 text-emerald-700">
              <span>🏷️</span> Khuyến Mãi
            </Link>
            <Link href="/tracking" className="hover:text-emerald-700 transition py-1 flex items-center gap-1">
              <span>📦</span> Tra Cứu Đơn
            </Link>
            <Link href="/#about" className="hover:text-emerald-700 transition py-1">
              Về Mộc Healthy
            </Link>
          </nav>

          {/* Action Buttons */}
          <div className="flex items-center space-x-2 sm:space-x-3">
            <Link
              href="/search"
              className="p-2 md:hidden text-slate-600 hover:text-emerald-700 text-base"
              title="Tìm kiếm"
            >
              🔍
            </Link>

            <Link
              href="/cart"
              className="flex items-center space-x-2 bg-emerald-50 hover:bg-emerald-100/80 text-emerald-800 px-3 py-2 rounded-xl text-xs font-bold transition border border-emerald-200"
            >
              <span className="text-sm">🛒</span>
              <span className="hidden sm:inline">Giỏ hàng</span>
              <span className="bg-emerald-600 text-white min-w-4 h-4 px-1 rounded-full text-[10px] flex items-center justify-center font-bold">
                {itemCount}
              </span>
            </Link>

            {/* Mobile Menu Toggle */}
            <button
              type="button"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="lg:hidden p-2 text-slate-700 hover:text-emerald-700 rounded-lg"
              aria-label="Toggle Menu"
            >
              <span className="text-xl">☰</span>
            </button>
          </div>
        </div>

        {/* Mobile Search Bar */}
        <div className="md:hidden px-4 pb-3">
          <form onSubmit={handleSearchSubmit} className="relative flex items-center">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Tìm táo, nước ép, sinh tố..."
              className="w-full pl-9 pr-16 py-2 rounded-xl text-xs bg-slate-100 border border-slate-200 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
            <span className="absolute left-3 text-slate-400 text-xs">🔍</span>
            <button
              type="submit"
              className="absolute right-1.5 px-2.5 py-1 bg-emerald-600 text-white rounded-lg text-[11px] font-bold"
            >
              Tìm
            </button>
          </form>
        </div>
      </header>

      {/* Mobile Drawer Menu */}
      {isMobileMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs"
            onClick={() => setIsMobileMenuOpen(false)}
          />
          <div className="fixed inset-y-0 right-0 max-w-xs w-full bg-white shadow-2xl p-6 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <span className="font-extrabold text-emerald-950 text-base">Menu Mộc Healthy</span>
                <button
                  type="button"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="p-1 text-slate-400 hover:text-slate-700 text-lg"
                >
                  ✕
                </button>
              </div>

              <nav className="py-6 space-y-4 text-sm font-semibold text-slate-700">
                <Link
                  href="/"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="block py-1 hover:text-emerald-700"
                >
                  🏠 Trang Chủ
                </Link>
                <Link
                  href="/search"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="block py-1 hover:text-emerald-700"
                >
                  🥑 Thực Đơn Đầy Đủ
                </Link>
                <Link
                  href="/promotions"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="block py-1 text-emerald-700 font-bold"
                >
                  🏷️ Chương Trình Khuyến Mãi
                </Link>
                <Link
                  href="/tracking"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="block py-1 hover:text-emerald-700"
                >
                  📦 Tra Cứu Đơn Hàng
                </Link>
                <Link
                  href="/#about"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="block py-1 hover:text-emerald-700"
                >
                  🌱 Cam Kết & Triết Lý Mộc
                </Link>
              </nav>
            </div>

            <div className="pt-6 border-t border-slate-100 space-y-2 text-xs text-slate-500">
              <div>Hotline giao hàng: <strong className="text-emerald-800">0901 234 567</strong></div>
              <div>Giờ hoạt động: 07:00 - 21:30</div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
