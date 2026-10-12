import React from 'react';
import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="max-w-xl mx-auto px-4 py-24 text-center space-y-6">
      <div className="w-24 h-24 mx-auto rounded-3xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-5xl shadow-sm">
        🥑
      </div>

      <div className="space-y-2">
        <span className="text-xs font-bold text-emerald-700 uppercase tracking-widest block">
          Lỗi 404 — Không Tìm Thấy Trang
        </span>
        <h1 className="text-2xl sm:text-4xl font-black text-slate-900 tracking-tight">
          Oops! Trang này không tồn tại
        </h1>
        <p className="text-xs sm:text-sm text-slate-600 max-w-md mx-auto leading-relaxed">
          Đường dẫn bạn vừa truy cập có thể đã được thay đổi hoặc tạm ngừng. Hãy quay về trang chủ hoặc khám phá thực đơn tươi ngon của Mộc Healthy nhé!
        </p>
      </div>

      <div className="flex items-center justify-center gap-3 pt-2">
        <Link
          href="/"
          className="bg-emerald-700 hover:bg-emerald-800 text-white font-extrabold px-5 py-2.5 rounded-2xl text-xs sm:text-sm transition shadow-sm"
        >
          🏠 Về Trang Chủ
        </Link>
        <Link
          href="/search"
          className="bg-white hover:bg-slate-50 text-slate-800 font-bold px-5 py-2.5 rounded-2xl text-xs sm:text-sm border border-slate-200 transition"
        >
          🥑 Khám Phá Thực Đơn
        </Link>
      </div>
    </div>
  );
}
