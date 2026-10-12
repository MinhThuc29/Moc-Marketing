'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import {
  Button,
  Input,
  Select,
  Badge,
  DataTable,
  Column,
  EmptyState,
  ErrorState,
  StatCard,
} from '@moc-healthy/ui';
import {
  ContentListItem,
  ContentCalendarItem,
  ContentOverviewStats,
  ContentDetailResponse,
} from '@moc-healthy/contracts';
import { AdminShell } from '../../components/shell/AdminShell';
import { PageHeader } from '../../components/shell/PageHeader';
import { useAuth } from '../../context/AuthContext';
import { contentApi } from '../../lib/api';
import { ContentDetailDrawer } from '../../components/content/ContentDetailDrawer';
import { ContentFormModal } from '../../components/content/ContentFormModal';
import { SocialPublishingManager } from '../../components/social/SocialPublishingManager';

const formatDate = (isoString?: string | null) => {
  if (!isoString) return '---';
  try {
    const d = new Date(isoString);
    return d.toLocaleDateString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return isoString;
  }
};

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'PUBLISHED':
      return <Badge variant="success">🚀 Đã xuất bản</Badge>;
    case 'SCHEDULED':
      return <Badge variant="info">📅 Đã lên lịch</Badge>;
    case 'IN_REVIEW':
      return <Badge variant="warning">⏳ Chờ duyệt</Badge>;
    case 'APPROVED':
      return <Badge variant="info">✅ Đã duyệt</Badge>;
    case 'AI_GENERATED':
      return <Badge variant="neutral">✨ Sinh bởi AI</Badge>;
    case 'DRAFT':
      return <Badge variant="neutral">📝 Bản nháp</Badge>;
    case 'FAILED':
      return <Badge variant="danger">❌ Thất bại</Badge>;
    case 'ARCHIVED':
      return <Badge variant="neutral">🗄️ Lưu trữ</Badge>;
    default:
      return <Badge variant="neutral">{status}</Badge>;
  }
};

const getChannelBadge = (channel: string) => {
  switch (channel) {
    case 'FACEBOOK':
      return <span className="text-blue-700 bg-blue-50 px-2 py-0.5 rounded font-semibold text-xs border border-blue-200">📘 Facebook</span>;
    case 'INSTAGRAM':
      return <span className="text-pink-700 bg-pink-50 px-2 py-0.5 rounded font-semibold text-xs border border-pink-200">📷 Instagram</span>;
    case 'TIKTOK':
      return <span className="text-slate-800 bg-slate-100 px-2 py-0.5 rounded font-semibold text-xs border border-slate-300">🎵 TikTok</span>;
    case 'ZALO':
      return <span className="text-sky-700 bg-sky-50 px-2 py-0.5 rounded font-semibold text-xs border border-sky-200">💬 Zalo OA</span>;
    case 'WEBSITE_BANNER':
      return <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-semibold text-xs border border-emerald-200">🌐 Web Banner</span>;
    default:
      return <span className="text-xs text-slate-600">{channel}</span>;
  }
};

const STATUS_TABS = [
  { key: '', label: 'Tất cả' },
  { key: 'PUBLISHED', label: '🚀 Đã xuất bản' },
  { key: 'SCHEDULED', label: '📅 Đã lên lịch' },
  { key: 'IN_REVIEW', label: '⏳ Chờ duyệt' },
  { key: 'APPROVED', label: '✅ Đã duyệt' },
  { key: 'DRAFT', label: '📝 Bản nháp' },
];

export default function ContentPage() {
  const { hasPermission } = useAuth();
  const canCreate = hasPermission('content.create');

  // View mode: 'list' | 'calendar' | 'social'
  const [viewMode, setViewMode] = useState<'list' | 'calendar' | 'social'>('list');

  // Stats
  const [stats, setStats] = useState<ContentOverviewStats | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [channelFilter, setChannelFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 10;

  // List Data
  const [contentItems, setContentItems] = useState<ContentListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  // Calendar Data
  const [calendarItems, setCalendarItems] = useState<ContentCalendarItem[]>([]);
  const [isCalendarLoading, setIsCalendarLoading] = useState(false);

  // Drawer & Modal
  const [selectedContentId, setSelectedContentId] = useState<string | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<ContentDetailResponse | null>(null);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
      setPage(1);
    }, 400);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  const loadStats = useCallback(async () => {
    try {
      const data = await contentApi.getOverview();
      setStats(data);
    } catch {
      // Fallback
    }
  }, []);

  const loadContent = useCallback(async () => {
    setIsLoading(true);
    setFetchError(null);
    try {
      const res = await contentApi.list({
        channel: channelFilter || undefined,
        status: statusFilter || undefined,
        search: debouncedSearch.trim() || undefined,
        page,
        page_size: pageSize,
      });
      setContentItems(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err: any) {
      setFetchError(err.message || 'Không thể tải danh sách bài viết');
    } finally {
      setIsLoading(false);
    }
  }, [channelFilter, statusFilter, debouncedSearch, page]);

  const loadCalendar = useCallback(async () => {
    setIsCalendarLoading(true);
    try {
      const data = await contentApi.getCalendar({
        channel: channelFilter || undefined,
        status: statusFilter || undefined,
      });
      setCalendarItems(data);
    } catch {
      // Fallback
    } finally {
      setIsCalendarLoading(false);
    }
  }, [channelFilter, statusFilter]);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  useEffect(() => {
    if (viewMode === 'list') {
      loadContent();
    } else if (viewMode === 'calendar') {
      loadCalendar();
    }
  }, [viewMode, loadContent, loadCalendar]);

  const handleOpenDetail = (id: string) => {
    setSelectedContentId(id);
    setIsDrawerOpen(true);
  };

  const handleCreateNew = () => {
    setEditingItem(null);
    setIsFormModalOpen(true);
  };

  const handleEdit = (it: ContentDetailResponse) => {
    setIsDrawerOpen(false);
    setEditingItem(it);
    setIsFormModalOpen(true);
  };

  const handleDeleteDraft = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Bạn có chắc muốn xóa bài viết này?')) return;
    try {
      await contentApi.delete(id);
      loadContent();
      loadStats();
    } catch (err: any) {
      alert(err.message || 'Không thể xóa bài viết');
    }
  };

  const columns: Column<ContentListItem>[] = [
    {
      key: 'title',
      header: 'Tiêu đề bài viết',
      render: (item) => (
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5">
            {item.ai_generated && (
              <span className="text-[10px] bg-purple-100 text-purple-800 font-bold px-1.5 py-0.2 rounded border border-purple-200">
                ✨ AI
              </span>
            )}
            <span className="font-semibold text-slate-900 group-hover:text-emerald-700 transition-colors">
              {item.title}
            </span>
          </div>
          <span className="text-xs text-slate-500 line-clamp-1 mt-0.5">{item.body_snippet}</span>
        </div>
      ),
    },
    {
      key: 'channel',
      header: 'Kênh',
      render: (item) => getChannelBadge(item.channel),
    },
    {
      key: 'status',
      header: 'Trạng thái',
      render: (item) => getStatusBadge(item.status),
    },
    {
      key: 'linked',
      header: 'Gắn kết',
      render: (item) => (
        <div className="flex flex-col text-xs text-slate-600">
          <span className="font-medium text-slate-800">{item.product_name || 'Toàn menu'}</span>
          <span className="text-[11px] text-slate-400">{item.campaign_name || 'Không có campaign'}</span>
        </div>
      ),
    },
    {
      key: 'schedule',
      header: 'Lịch phát hành',
      render: (item) => (
        <span className="text-xs text-slate-700 font-medium">
          {item.published_at
            ? `Đã đăng: ${formatDate(item.published_at)}`
            : item.scheduled_at
            ? `Lịch: ${formatDate(item.scheduled_at)}`
            : formatDate(item.created_at)}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Thao tác',
      render: (item) => (
        <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleOpenDetail(item.id)}
            className="text-xs py-1 px-2.5"
          >
            Chi tiết
          </Button>
          {item.status !== 'PUBLISHED' && canCreate && (
            <Button
              variant="danger"
              size="sm"
              onClick={(e) => handleDeleteDraft(item.id, e)}
              className="text-xs py-1 px-2"
              title="Xóa bài viết"
            >
              🗑️
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <AdminShell requiredPermission="content.create">
      <div className="space-y-6">
        <PageHeader
          title="Quản lý Nội dung & Lịch phát hành"
          subtitle="Kho bài viết tiếp thị, sáng tạo nội dung tự động, phê duyệt Human-in-the-loop và tự động xuất bản đa kênh"
          breadcrumbs={[{ label: 'Content Hub' }]}
          actions={
            <div className="flex items-center gap-2">
              <Link href="/ai-studio">
                <Button variant="outline" size="sm" className="bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-100">
                  ✨ AI Content Studio
                </Button>
              </Link>
              {canCreate && (
                <Button variant="primary" size="sm" onClick={handleCreateNew}>
                  + Tạo bài viết mới
                </Button>
              )}
            </div>
          }
        />

        {/* Overview Stats */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <StatCard
            title="Tổng nội dung"
            value={stats ? `${stats.total_items} bài` : '---'}
            period="Toàn bộ kho nội dung"
          />
          <StatCard
            title="Đã xuất bản"
            value={stats ? `${stats.published_items}` : '---'}
            period="Đang chạy trên MXH"
          />
          <StatCard
            title="Đã lên lịch"
            value={stats ? `${stats.scheduled_items}` : '---'}
            period="Chờ tự động đăng"
          />
          <StatCard
            title="Đang chờ duyệt"
            value={stats ? `${stats.in_review_items}` : '---'}
            period="Cần duyệt trước khi đăng"
          />
          <StatCard
            title="Sinh bởi AI"
            value={stats ? `${stats.ai_generated_items}` : '---'}
            period="AI Content Studio"
          />
        </div>

        {/* View Switcher & Filters */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-4 shadow-xs">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-3">
            {/* View Mode Switcher */}
            <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg">
              <button
                type="button"
                onClick={() => setViewMode('list')}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                  viewMode === 'list'
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                📋 Danh sách bài viết
              </button>
              <button
                type="button"
                onClick={() => setViewMode('calendar')}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                  viewMode === 'calendar'
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                📅 Lịch phát hành (Calendar)
              </button>
              <button
                type="button"
                onClick={() => setViewMode('social')}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                  viewMode === 'social'
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                🌐 Kênh MXH & Hàng đợi
              </button>
            </div>

            {/* Status Tabs for List View */}
            {viewMode === 'list' && (
              <div className="flex overflow-x-auto pb-1 gap-1">
                {STATUS_TABS.map((tab) => {
                  const isActive = statusFilter === tab.key;
                  return (
                    <button
                      key={tab.key}
                      type="button"
                      onClick={() => {
                        setStatusFilter(tab.key);
                        setPage(1);
                      }}
                      className={`px-2.5 py-1 text-xs font-medium rounded-full transition-colors whitespace-nowrap ${
                        isActive
                          ? 'bg-emerald-600 text-white font-bold'
                          : 'bg-slate-50 text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      {tab.label}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Search & Channel Dropdown (only for list and calendar) */}
          {viewMode !== 'social' && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="sm:col-span-2">
                <Input
                  placeholder="🔍 Tìm kiếm bài viết theo tiêu đề, hook, nội dung..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              <div>
                <Select
                  value={channelFilter}
                  onChange={(e) => {
                    setChannelFilter(e.target.value);
                    setPage(1);
                  }}
                  options={[
                    { value: '', label: 'Tất cả các kênh' },
                    { value: 'FACEBOOK', label: '📘 Facebook' },
                    { value: 'INSTAGRAM', label: '📷 Instagram' },
                    { value: 'TIKTOK', label: '🎵 TikTok' },
                    { value: 'ZALO', label: '💬 Zalo OA' },
                    { value: 'WEBSITE_BANNER', label: '🌐 Website Banner' },
                  ]}
                />
              </div>
            </div>
          )}
        </div>

        {/* Content View: List, Calendar or Social Publishing */}
        {viewMode === 'social' ? (
          <SocialPublishingManager />
        ) : viewMode === 'list' ? (
          fetchError ? (
            <ErrorState
              title="Lỗi tải danh sách nội dung"
              message={fetchError}
              onRetry={loadContent}
            />
          ) : contentItems.length === 0 && !isLoading ? (
            <EmptyState
              title="Chưa có bài viết nào"
              description={
                searchTerm || statusFilter || channelFilter
                  ? 'Không tìm thấy bài viết nào khớp với bộ lọc.'
                  : 'Hãy bắt đầu sáng tạo bài viết mới hoặc sử dụng AI Studio để sinh tự động.'
              }
              icon="📝"
              actionText={canCreate ? '+ Tạo bài viết đầu tiên' : undefined}
              onAction={canCreate ? handleCreateNew : undefined}
            />
          ) : (
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
              <DataTable<ContentListItem>
                columns={columns}
                data={contentItems}
                keyExtractor={(item: ContentListItem) => item.id}
                isLoading={isLoading}
                currentPage={page}
                totalPages={totalPages}
                onPageChange={(p: number) => setPage(p)}
              />
            </div>
          )
        ) : (
          /* Calendar View */
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
            <div className="flex justify-between items-center mb-4 pb-2 border-b border-slate-200">
              <h3 className="text-sm font-bold text-slate-800">
                Lịch phát hành bài viết trong tháng (30 ngày)
              </h3>
              <span className="text-xs text-slate-500 font-medium">
                Tổng cộng {calendarItems.length} bài đã lên lịch / đã đăng
              </span>
            </div>

            {isCalendarLoading ? (
              <div className="py-12 text-center text-sm text-slate-500 animate-pulse">
                Đang tải dữ liệu lịch phát hành...
              </div>
            ) : calendarItems.length === 0 ? (
              <div className="py-12 text-center text-slate-400 text-xs italic">
                Chưa có bài viết nào được lên lịch hoặc đã đăng trong khung thời gian này.
              </div>
            ) : (
              <div className="space-y-3">
                {calendarItems.map((cItem) => (
                  <div
                    key={cItem.id}
                    onClick={() => handleOpenDetail(cItem.id)}
                    className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 bg-slate-50/70 hover:bg-emerald-50/50 border border-slate-200 rounded-xl transition-all cursor-pointer gap-2"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-lg bg-white border border-slate-200 flex flex-col items-center justify-center text-center shadow-2xs">
                        <span className="text-[10px] font-bold text-slate-400 uppercase">
                          {cItem.scheduled_at ? new Date(cItem.scheduled_at).toLocaleDateString('vi-VN', { month: 'numeric' }) : '---'}
                        </span>
                        <span className="text-sm font-extrabold text-slate-800">
                          {cItem.scheduled_at ? new Date(cItem.scheduled_at).getDate() : '--'}
                        </span>
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          {getChannelBadge(cItem.channel)}
                          <span className="font-bold text-xs text-slate-900">{cItem.title}</span>
                        </div>
                        <div className="flex items-center gap-2 mt-1 text-[11px] text-slate-500">
                          <span>{cItem.product_name || 'Toàn menu'}</span>
                          {cItem.campaign_name && <span>• {cItem.campaign_name}</span>}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2.5 sm:self-center">
                      <span className="text-xs text-slate-500 font-mono font-medium">
                        {formatDate(cItem.scheduled_at || cItem.published_at)}
                      </span>
                      {getStatusBadge(cItem.status)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Drawer Detail */}
        <ContentDetailDrawer
          isOpen={isDrawerOpen}
          onClose={() => setIsDrawerOpen(false)}
          contentId={selectedContentId}
          onContentUpdated={() => {
            loadContent();
            loadCalendar();
            loadStats();
          }}
          onEdit={handleEdit}
        />

        {/* Form Modal */}
        <ContentFormModal
          isOpen={isFormModalOpen}
          onClose={() => {
            setIsFormModalOpen(false);
            setEditingItem(null);
          }}
          item={editingItem}
          onSuccess={() => {
            loadContent();
            loadCalendar();
            loadStats();
          }}
        />
      </div>
    </AdminShell>
  );
}
