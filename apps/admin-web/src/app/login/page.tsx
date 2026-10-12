'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../context/AuthContext';
import { Card, Button, Badge } from '@moc-healthy/ui';

export default function LoginPage() {
  const { login, user } = useAuth();
  const router = useRouter();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // If already logged in, redirect
  React.useEffect(() => {
    if (user) {
      router.push('/');
    }
  }, [user, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const result = await login(email, password);
    setIsSubmitting(false);

    if (result.success) {
      router.push('/');
    } else {
      setError(result.error || 'Đăng nhập không thành công');
    }
  };

  const handleQuickFill = (demoEmail: string) => {
    setEmail(demoEmail);
    setPassword('Password@123');
    setError(null);
  };

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full space-y-6">
        {/* Brand header */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-xl bg-emerald-700 flex items-center justify-center text-white font-extrabold text-2xl mx-auto shadow-md">
            M
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Mộc Healthy Portal</h1>
          <p className="text-xs text-slate-600">Đăng nhập tài khoản quản trị vận hành & marketing</p>
        </div>

        <Card className="p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700 font-medium">
                {error}
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Email công việc
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@mochhealthy.vn"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Mật khẩu
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition"
              />
            </div>

            <Button
              type="submit"
              variant="primary"
              size="md"
              className="w-full justify-center"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Đang xác thực...' : 'Đăng nhập vào hệ thống'}
            </Button>
          </form>

          {/* Seed demo quick-fill helper */}
          <div className="mt-6 pt-4 border-t border-slate-100">
            <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
              Tài khoản mẫu kiểm thử RBAC:
            </p>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => handleQuickFill('admin@mochhealthy.vn')}
                className="px-2.5 py-1 text-xs bg-slate-50 hover:bg-emerald-50 hover:text-emerald-800 border border-slate-200 rounded-md transition text-slate-700 font-medium"
              >
                Admin
              </button>
              <button
                type="button"
                onClick={() => handleQuickFill('marketing@mochhealthy.vn')}
                className="px-2.5 py-1 text-xs bg-slate-50 hover:bg-emerald-50 hover:text-emerald-800 border border-slate-200 rounded-md transition text-slate-700 font-medium"
              >
                Marketing
              </button>
              <button
                type="button"
                onClick={() => handleQuickFill('inventory@mochhealthy.vn')}
                className="px-2.5 py-1 text-xs bg-slate-50 hover:bg-emerald-50 hover:text-emerald-800 border border-slate-200 rounded-md transition text-slate-700 font-medium"
              >
                Thủ kho
              </button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
