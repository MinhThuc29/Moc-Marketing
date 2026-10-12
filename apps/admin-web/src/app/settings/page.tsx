'use client';

import React, { useState } from 'react';
import { AdminShell } from '../../components/shell/AdminShell';
import { PageHeader } from '../../components/shell/PageHeader';
import { EmptyState } from '@moc-healthy/ui';
import { SocialPublishingManager } from '../../components/social/SocialPublishingManager';
import { AIProviderManager } from '../../components/ai/AIProviderManager';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<'SOCIAL' | 'USERS' | 'AUDIT' | 'AI'>('SOCIAL');

  return (
    <AdminShell requiredPermission="settings.manage">
      <div className="space-y-6">
        <PageHeader
          title="Cài đặt Hệ thống & Kết nối API"
          subtitle="Quản trị kết nối mạng xã hội đa kênh, hạ tầng API nhà cung cấp, người dùng và phân quyền RBAC"
          breadcrumbs={[{ label: 'Cài đặt' }]}
        />

        {/* Navigation Tabs */}
        <div className="bg-white rounded-xl border border-slate-200/90 p-1.5 flex flex-wrap gap-1 shadow-2xs">
          <button
            onClick={() => setActiveTab('SOCIAL')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 ${
              activeTab === 'SOCIAL'
                ? 'bg-emerald-600 text-white shadow-xs'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <span>🌐</span>
            <span>Kênh MXH & Social Publishing</span>
          </button>

          <button
            onClick={() => setActiveTab('AI')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 ${
              activeTab === 'AI'
                ? 'bg-emerald-600 text-white shadow-xs'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <span>🤖</span>
            <span>Cấu hình AI Provider</span>
          </button>

          <button
            onClick={() => setActiveTab('USERS')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 ${
              activeTab === 'USERS'
                ? 'bg-emerald-600 text-white shadow-xs'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <span>👥</span>
            <span>Người dùng & Phân quyền (RBAC)</span>
          </button>

          <button
            onClick={() => setActiveTab('AUDIT')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 ${
              activeTab === 'AUDIT'
                ? 'bg-emerald-600 text-white shadow-xs'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <span>📜</span>
            <span>Audit Log</span>
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'SOCIAL' && (
          <div className="space-y-4">
            <SocialPublishingManager />
          </div>
        )}

        {activeTab === 'AI' && (
          <div className="space-y-4">
            <AIProviderManager />
          </div>
        )}

        {activeTab === 'USERS' && (
          <EmptyState
            title="Phân hệ Quản trị Người dùng & Phân quyền RBAC"
            description="Module này quản lý danh sách nhân sự, phân nhóm quyền (Admin, Marketer, Manager, Staff) tại PROMPT 34 & 35."
            icon="👥"
          />
        )}

        {activeTab === 'AUDIT' && (
          <EmptyState
            title="Nhật ký Hoạt động Hệ thống (Audit Log)"
            description="Ghi nhận dấu vết tất cả các thao tác nhạy cảm: xuất bản bài viết, thay đổi đơn hàng, cấp quyền nhân sự."
            icon="📜"
          />
        )}
      </div>
    </AdminShell>
  );
}
