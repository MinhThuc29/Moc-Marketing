'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@moc-healthy/ui';

export default function UnauthorizedPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white p-8 rounded-2xl border border-slate-200 text-center space-y-4 shadow-sm">
        <div className="w-16 h-16 bg-rose-50 text-rose-600 rounded-2xl flex items-center justify-center mx-auto text-2xl font-bold">
          403
        </div>
        <h1 className="text-2xl font-bold text-slate-900">Truy cập bị từ chối</h1>
        <p className="text-sm text-slate-600">
          Bạn không có quyền hạn cần thiết để truy cập tài nguyên này. Nếu bạn cần quyền hạn, vui lòng liên hệ quản trị viên (Admin).
        </p>
        <div className="pt-2 flex justify-center gap-3">
          <Button variant="primary" onClick={() => router.push('/')}>
            Trang chủ Quản trị
          </Button>
          <Button variant="outline" onClick={() => router.push('/login')}>
            Đăng nhập lại
          </Button>
        </div>
      </div>
    </div>
  );
}
