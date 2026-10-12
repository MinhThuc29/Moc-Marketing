'use client';

import React, { useState, useEffect } from 'react';
import { Drawer, Button, Badge, Input } from '@moc-healthy/ui';
import { ContentDetailResponse } from '@moc-healthy/contracts';
import { contentApi, socialApi } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';

export interface ContentDetailDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  contentId: string | null;
  onContentUpdated?: () => void;
  onEdit?: (item: ContentDetailResponse) => void;
}

const formatDate = (isoString?: string | null) => {
  if (!isoString) return '---';
  try {
    const d = new Date(isoString);
    return d.toLocaleDateString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
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
      return <Badge variant="danger">❌ Lỗi xuất bản</Badge>;
    case 'ARCHIVED':
      return <Badge variant="neutral">🗄️ Lưu trữ</Badge>;
    default:
      return <Badge variant="neutral">{status}</Badge>;
  }
};

const getChannelIcon = (channel: string) => {
  switch (channel) {
    case 'FACEBOOK':
      return '📘 Facebook Post';
    case 'ZALO':
      return '💬 Zalo OA / ZNS';
    case 'TIKTOK':
      return '🎵 TikTok Short Video';
    case 'INSTAGRAM':
      return '📷 Instagram Post';
    case 'WEBSITE_BANNER':
      return '🌐 Website Banner';
    default:
      return channel;
  }
};

export const ContentDetailDrawer: React.FC<ContentDetailDrawerProps> = ({
  isOpen,
  onClose,
  contentId,
  onContentUpdated,
  onEdit,
}) => {
  const { hasPermission } = useAuth();
  const canCreate = hasPermission('content.create');
  const canApprove = hasPermission('content.approve');
  const canPublish = hasPermission('content.publish');

  const [item, setItem] = useState<ContentDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Schedule modal state
  const [showScheduleInput, setShowScheduleInput] = useState(false);
  const [scheduleDateTime, setScheduleDateTime] = useState('');

  useEffect(() => {
    if (isOpen && contentId) {
      loadDetail(contentId);
      setShowScheduleInput(false);
    } else {
      setItem(null);
      setErrorMsg(null);
    }
  }, [isOpen, contentId]);

  const loadDetail = async (id: string) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const data = await contentApi.get(id);
      setItem(data);
    } catch (err: any) {
      setErrorMsg(err.message || 'Không thể tải chi tiết nội dung');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAction = async (actionFn: () => Promise<any>) => {
    setActionLoading(true);
    setErrorMsg(null);
    try {
      await actionFn();
      if (contentId) await loadDetail(contentId);
      if (onContentUpdated) onContentUpdated();
    } catch (err: any) {
      setErrorMsg(err.message || 'Thao tác không thành công');
    } finally {
      setActionLoading(false);
    }
  };

  const handleScheduleSubmit = async () => {
    if (!scheduleDateTime || !contentId) return;
    await handleAction(() => contentApi.schedule(contentId, new Date(scheduleDateTime).toISOString()));
    setShowScheduleInput(false);
  };

  if (!isOpen) return null;

  return (
    <Drawer
      isOpen={isOpen}
      onClose={onClose}
      title={item ? `Nội dung: ${item.title}` : 'Chi tiết bài viết'}
      maxWidth="xl"
    >
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-20 space-y-3">
          <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-slate-500">Đang tải dữ liệu bài viết...</p>
        </div>
      ) : errorMsg && !item ? (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-sm">
          {errorMsg}
        </div>
      ) : item ? (
        <div className="space-y-6 pb-12">
          {errorMsg && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded text-rose-700 text-xs">
              {errorMsg}
            </div>
          )}

          {/* Header Card */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-5">
            <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
              <span className="font-semibold text-xs px-2.5 py-1 bg-white border border-slate-200 text-slate-800 rounded-lg shadow-2xs">
                {getChannelIcon(item.channel)}
              </span>
              <div className="flex items-center gap-2">
                {item.ai_generated && (
                  <span className="px-2 py-0.5 bg-purple-100 text-purple-800 font-bold rounded text-[11px] border border-purple-200">
                    ✨ AI Generated
                  </span>
                )}
                {getStatusBadge(item.status)}
              </div>
            </div>

            <h2 className="text-lg font-bold text-slate-900 mt-2">{item.title}</h2>

            <div className="grid grid-cols-2 gap-4 mt-4 text-xs text-slate-600 border-t border-slate-200 pt-3">
              <div>
                <span className="text-slate-400 block">Sản phẩm liên kết:</span>
                <span className="font-semibold text-emerald-800">{item.product_name || 'Toàn menu'}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Chiến dịch tiếp thị:</span>
                <span className="font-semibold text-slate-800">{item.campaign_name || 'Không gắn campaign'}</span>
              </div>
            </div>
          </div>

          {/* Social Post Mockup Preview */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
              Xem trước hiển thị mạng xã hội (Post Preview)
            </h3>
            <div className="bg-white border-2 border-slate-200 rounded-2xl p-4 shadow-xs space-y-3">
              {/* Channel Profile Header */}
              <div className="flex items-center gap-3 border-b border-slate-100 pb-2.5">
                <div className="w-9 h-9 rounded-full bg-emerald-600 text-white flex items-center justify-center font-black text-sm">
                  M
                </div>
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-xs text-slate-900">Mộc Healthy - Bữa Ăn Xanh</span>
                    <span className="text-blue-500 text-xs">✓</span>
                  </div>
                  <span className="text-[10px] text-slate-400">
                    {item.published_at ? formatDate(item.published_at) : 'Bản xem trước'} • 🌐
                  </span>
                </div>
              </div>

              {/* Post Hook */}
              {item.hook && (
                <p className="text-sm font-bold text-slate-900 bg-emerald-50/60 p-2.5 rounded-lg border-l-4 border-emerald-500">
                  {item.hook}
                </p>
              )}

              {/* Post Body */}
              <p className="text-xs text-slate-800 leading-relaxed whitespace-pre-line font-sans">
                {item.body}
              </p>

              {/* CTA */}
              {item.cta && (
                <div className="p-2.5 bg-amber-50 rounded-lg border border-amber-200 text-xs font-semibold text-amber-900">
                  👉 {item.cta}
                </div>
              )}

              {/* Hashtags */}
              {item.hashtags && item.hashtags.length > 0 && (
                <div className="flex flex-wrap gap-1 pt-1">
                  {item.hashtags.map((tag) => (
                    <span key={tag} className="text-[11px] font-semibold text-blue-600">
                      {tag.startsWith('#') ? tag : `#${tag}`}
                    </span>
                  ))}
                </div>
              )}

              {/* Published URL link */}
              {item.external_post_url && (
                <div className="mt-2 pt-2 border-t border-slate-100 text-xs flex justify-between items-center">
                  <span className="text-slate-400">Bài đăng thực tế:</span>
                  <a
                    href={item.external_post_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-emerald-700 hover:underline font-mono truncate max-w-[280px]"
                  >
                    🔗 {item.external_post_url}
                  </a>
                </div>
              )}
            </div>
          </div>

          {/* Social Metrics (if published) */}
          {item.status === 'PUBLISHED' && item.metrics && Object.keys(item.metrics).length > 0 && (
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                Chỉ số tương tác ban đầu (Social Metrics)
              </h3>
              <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
                {Object.entries(item.metrics).map(([key, val]) => (
                  <div key={key} className="bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-center">
                    <span className="text-[10px] uppercase text-slate-400 block font-semibold">{key}</span>
                    <span className="text-sm font-bold text-slate-800">{String(val)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Schedule Input Box if active */}
          {showScheduleInput && (
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl space-y-3">
              <span className="text-xs font-bold text-emerald-900 block">Chọn thời gian lên lịch đăng bài:</span>
              <Input
                type="datetime-local"
                value={scheduleDateTime}
                onChange={(e) => setScheduleDateTime(e.target.value)}
              />
              <div className="flex justify-end gap-2">
                <Button size="sm" variant="outline" onClick={() => setShowScheduleInput(false)}>
                  Hủy
                </Button>
                <Button size="sm" variant="primary" onClick={handleScheduleSubmit} disabled={actionLoading}>
                  Xác nhận lên lịch
                </Button>
              </div>
            </div>
          )}

          {/* Audit trail */}
          <div className="text-[11px] text-slate-400 border-t border-slate-200 pt-3 space-y-1">
            <div>
              <span>Tạo bởi: </span>
              <span className="text-slate-600 font-medium">{item.created_by_user_name || 'Hệ thống'}</span>
              <span> vào lúc {formatDate(item.created_at)}</span>
            </div>
            {item.approved_at && (
              <div>
                <span>Phê duyệt bởi: </span>
                <span className="text-slate-600 font-medium">{item.approved_by_user_name || 'Quản lý'}</span>
                <span> vào lúc {formatDate(item.approved_at)}</span>
              </div>
            )}
            {item.scheduled_at && (
              <div>
                <span>Dự kiến đăng vào lúc: </span>
                <span className="text-slate-700 font-bold">{formatDate(item.scheduled_at)}</span>
              </div>
            )}
            {item.published_at && (
              <div>
                <span>Đã đăng vào lúc: </span>
                <span className="text-emerald-700 font-bold">{formatDate(item.published_at)}</span>
              </div>
            )}
          </div>

          {/* Actions Bar */}
          <div className="border-t border-slate-200 pt-4 flex flex-wrap gap-2 justify-end">
            {['DRAFT', 'AI_GENERATED'].includes(item.status) && canCreate && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onEdit && onEdit(item)}
                  disabled={actionLoading}
                >
                  ✏️ Chỉnh sửa
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  disabled={actionLoading}
                  onClick={() => handleAction(() => contentApi.submitReview(item.id))}
                >
                  📨 Gửi duyệt bài viết
                </Button>
              </>
            )}

            {item.status === 'IN_REVIEW' && canApprove && (
              <Button
                variant="primary"
                size="sm"
                className="bg-emerald-600 hover:bg-emerald-700"
                disabled={actionLoading}
                onClick={() => handleAction(() => contentApi.approve(item.id))}
              >
                ✅ Phê duyệt bài viết
              </Button>
            )}

            {item.status === 'APPROVED' && canPublish && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={actionLoading}
                  onClick={() => setShowScheduleInput(true)}
                >
                  📅 Lên lịch đăng
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  className="bg-emerald-600 hover:bg-emerald-700"
                  disabled={actionLoading}
                  onClick={() => handleAction(() => socialApi.publishNow(item.id))}
                >
                  🚀 Xuất bản ngay
                </Button>
              </>
            )}

            {item.status === 'SCHEDULED' && canPublish && (
              <Button
                variant="primary"
                size="sm"
                className="bg-emerald-600 hover:bg-emerald-700"
                disabled={actionLoading}
                onClick={() => handleAction(() => socialApi.publishNow(item.id))}
              >
                🚀 Xuất bản ngay lập tức
              </Button>
            )}

            {item.status !== 'PUBLISHED' && canCreate && (
              <Button
                variant="danger"
                size="sm"
                disabled={actionLoading}
                onClick={() => handleAction(() => contentApi.delete(item.id))}
              >
                Xóa bài
              </Button>
            )}
          </div>
        </div>
      ) : null}
    </Drawer>
  );
};
