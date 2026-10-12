'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Button,
  Badge,
  DataTable,
  Column,
  EmptyState,
  StatCard,
} from '@moc-healthy/ui';
import type {
  SocialConnectionItem,
  PublishedPostItem,
  WorkerBatchResult,
} from '@moc-healthy/contracts';
import { socialApi } from '../../lib/api';

const getPlatformIcon = (platform: string) => {
  switch (platform.toUpperCase()) {
    case 'FACEBOOK':
      return { icon: '📘', name: 'Facebook Fanpage', color: 'bg-blue-50 text-blue-700 border-blue-200' };
    case 'INSTAGRAM':
      return { icon: '📸', name: 'Instagram Business', color: 'bg-pink-50 text-pink-700 border-pink-200' };
    case 'TIKTOK':
      return { icon: '🎵', name: 'TikTok Creator', color: 'bg-slate-900 text-white border-slate-700' };
    case 'ZALO_OA':
    case 'ZALO':
      return { icon: '💬', name: 'Zalo Official Account', color: 'bg-sky-50 text-sky-700 border-sky-200' };
    case 'WEBSITE_BLOG':
    case 'WEBSITE_BANNER':
      return { icon: '🌐', name: 'Website Storefront Blog', color: 'bg-emerald-50 text-emerald-800 border-emerald-200' };
    default:
      return { icon: '📱', name: platform, color: 'bg-slate-50 text-slate-700 border-slate-200' };
  }
};

const getStatusBadge = (status: string) => {
  switch (status.toUpperCase()) {
    case 'CONNECTED':
      return <Badge variant="success">🟢 Đang kết nối</Badge>;
    case 'EXPIRED':
      return <Badge variant="warning">⚠️ Token hết hạn</Badge>;
    case 'ERROR':
      return <Badge variant="danger">❌ Lỗi kết nối</Badge>;
    case 'DISCONNECTED':
      return <Badge variant="neutral">⚪ Đã ngắt kết nối</Badge>;
    case 'PUBLISHED':
      return <Badge variant="success">🚀 Đã xuất bản</Badge>;
    case 'PUBLISHING':
      return <Badge variant="info">⏳ Đang gửi API...</Badge>;
    case 'FAILED':
      return <Badge variant="danger">❌ Thất bại</Badge>;
    case 'QUEUED':
    case 'PENDING':
      return <Badge variant="neutral">🕒 Chờ trong hàng đợi</Badge>;
    default:
      return <Badge variant="neutral">{status}</Badge>;
  }
};

export const SocialPublishingManager: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState<'CONNECTIONS' | 'LOGS'>('CONNECTIONS');

  // Connections State
  const [connections, setConnections] = useState<SocialConnectionItem[]>([]);
  const [isLoadingConnections, setIsLoadingConnections] = useState(true);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [refreshingId, setRefreshingId] = useState<string | null>(null);
  const [feedbackMsg, setFeedbackMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Publishing Logs State
  const [publishedPosts, setPublishedPosts] = useState<PublishedPostItem[]>([]);
  const [totalPosts, setTotalPosts] = useState(0);
  const [isLoadingPosts, setIsLoadingPosts] = useState(false);
  const [retryingId, setRetryingId] = useState<string | null>(null);
  const [syncingId, setSyncingId] = useState<string | null>(null);
  const [isWorkerRunning, setIsWorkerRunning] = useState(false);
  const [workerResult, setWorkerResult] = useState<WorkerBatchResult | null>(null);

  // -------------------------------------------------------------
  // Data Loaders
  // -------------------------------------------------------------

  const loadConnections = useCallback(async () => {
    setIsLoadingConnections(true);
    try {
      const data = await socialApi.listConnections();
      setConnections(data);
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: err.message || 'Không thể tải danh sách kết nối.' });
    } finally {
      setIsLoadingConnections(false);
    }
  }, []);

  const loadPublishedPosts = useCallback(async () => {
    setIsLoadingPosts(true);
    try {
      const res = await socialApi.listPublishedPosts({ limit: 50 });
      setPublishedPosts(res.items);
      setTotalPosts(res.total);
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: err.message || 'Không thể tải nhật ký xuất bản.' });
    } finally {
      setIsLoadingPosts(false);
    }
  }, []);

  useEffect(() => {
    if (activeSubTab === 'CONNECTIONS') {
      loadConnections();
    } else {
      loadPublishedPosts();
    }
  }, [activeSubTab, loadConnections, loadPublishedPosts]);

  // -------------------------------------------------------------
  // Actions: Connections
  // -------------------------------------------------------------

  const handleTestConnection = async (id: string) => {
    setTestingId(id);
    setFeedbackMsg(null);
    try {
      const res = await socialApi.testConnection(id);
      if (res.is_valid) {
        setFeedbackMsg({ type: 'success', text: `Kiểm tra kết nối thành công: ${res.message}` });
      } else {
        setFeedbackMsg({ type: 'error', text: `Lỗi kết nối: ${res.message}` });
      }
      await loadConnections();
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: err.message || 'Lỗi khi kiểm tra kết nối.' });
    } finally {
      setTestingId(null);
    }
  };

  const handleRefreshToken = async (id: string) => {
    setRefreshingId(id);
    setFeedbackMsg(null);
    try {
      const res = await socialApi.refreshToken(id);
      if (res.success) {
        setFeedbackMsg({ type: 'success', text: `Đã làm mới OAuth Access Token thành công!` });
      } else {
        setFeedbackMsg({ type: 'error', text: res.message });
      }
      await loadConnections();
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: err.message || 'Lỗi khi làm mới token.' });
    } finally {
      setRefreshingId(null);
    }
  };

  const handleDisconnect = async (id: string, name: string) => {
    if (!confirm(`Bạn có chắc muốn ngắt kết nối tài khoản "${name}"?`)) return;
    try {
      await socialApi.disconnect(id);
      setFeedbackMsg({ type: 'success', text: `Đã ngắt kết nối tài khoản "${name}".` });
      await loadConnections();
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: err.message || 'Không thể ngắt kết nối.' });
    }
  };

  // -------------------------------------------------------------
  // Actions: Publishing Logs & Worker
  // -------------------------------------------------------------

  const handleRunWorker = async () => {
    setIsWorkerRunning(true);
    setFeedbackMsg(null);
    try {
      const res = await socialApi.runWorkerBatch(15);
      setWorkerResult(res);
      setFeedbackMsg({
        type: 'success',
        text: `Background Worker đã quét ${res.processed} bài: Xuất bản thành công ${res.published}, Thử lại ${res.retried}, Lỗi ${res.failed}.`,
      });
      await loadPublishedPosts();
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: err.message || 'Không thể chạy Background Worker.' });
    } finally {
      setIsWorkerRunning(false);
    }
  };

  const handleRetryPost = async (id: string) => {
    setRetryingId(id);
    try {
      const res = await socialApi.retryPost(id);
      if (res.publish_status === 'PUBLISHED') {
        setFeedbackMsg({ type: 'success', text: `Thử lại xuất bản bài viết thành công!` });
      } else {
        setFeedbackMsg({ type: 'error', text: `Thử lại thất bại: ${res.error_message}` });
      }
      await loadPublishedPosts();
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: err.message || 'Không thể thử lại xuất bản.' });
    } finally {
      setRetryingId(null);
    }
  };

  const handleSyncMetrics = async (id: string) => {
    setSyncingId(id);
    try {
      const res = await socialApi.syncMetrics(id);
      setFeedbackMsg({
        type: 'success',
        text: `Đồng bộ tương tác thành công: ${res.impressions} hiển thị, ${res.reach} tiếp cận, ${res.likes} lượt thích.`,
      });
      await loadPublishedPosts();
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: err.message || 'Không thể đồng bộ chỉ số.' });
    } finally {
      setSyncingId(null);
    }
  };

  // -------------------------------------------------------------
  // Columns for Published Posts Table
  // -------------------------------------------------------------

  const columns: Column<PublishedPostItem>[] = [
    {
      key: 'channel',
      header: 'Kênh xuất bản',
      render: (item) => {
        const info = getPlatformIcon(item.channel);
        return (
          <div className="flex items-center gap-2">
            <span className="text-base">{info.icon}</span>
            <div>
              <p className="font-bold text-xs text-slate-800">{info.name}</p>
              <p className="text-[10px] text-slate-400 font-mono">{item.external_post_id || 'Chưa cấp ID'}</p>
            </div>
          </div>
        );
      },
    },
    {
      key: 'title',
      header: 'Nội dung bài viết',
      render: (item) => (
        <div className="max-w-md">
          <p className="font-semibold text-xs text-slate-900 truncate">
            {item.payload_snapshot?.title || 'Bài viết tiếp thị'}
          </p>
          <p className="text-[11px] text-slate-500 line-clamp-1 mt-0.5">
            {item.payload_snapshot?.body || ''}
          </p>
        </div>
      ),
    },
    {
      key: 'publish_status',
      header: 'Trạng thái',
      render: (item) => (
        <div className="space-y-1">
          {getStatusBadge(item.publish_status)}
          {item.error_message && (
            <p className="text-[10px] text-rose-600 line-clamp-1 max-w-xs" title={item.error_message}>
              {item.error_message}
            </p>
          )}
          {item.retry_count > 0 && item.publish_status === 'FAILED' && (
            <p className="text-[9px] text-slate-400">
              Đã thử: {item.retry_count}/{item.max_retries} lần
            </p>
          )}
        </div>
      ),
    },
    {
      key: 'published_at',
      header: 'Thời gian',
      render: (item) => (
        <div className="text-[11px] text-slate-600">
          {item.published_at ? (
            <span>{new Date(item.published_at).toLocaleString('vi-VN')}</span>
          ) : item.scheduled_at ? (
            <span className="text-amber-700">Hẹn giờ: {new Date(item.scheduled_at).toLocaleString('vi-VN')}</span>
          ) : (
            <span className="text-slate-400">---</span>
          )}
        </div>
      ),
    },
    {
      key: 'metrics',
      header: 'Chỉ số tương tác',
      render: (item) => {
        const m = item.latest_metric;
        if (!m) return <span className="text-xs text-slate-400">Chưa có số liệu</span>;
        return (
          <div className="flex items-center gap-3 text-[11px] text-slate-700">
            <span title="Lượt xem / Hiển thị">👁️ {m.impressions.toLocaleString()}</span>
            <span title="Lượt tiếp cận">👥 {m.reach.toLocaleString()}</span>
            <span title="Lượt thích">❤️ {m.likes.toLocaleString()}</span>
            <span title="Chia sẻ">🔄 {m.shares.toLocaleString()}</span>
          </div>
        );
      },
    },
    {
      key: 'actions',
      header: 'Thao tác',
      render: (item) => (
        <div className="flex items-center gap-2">
          {item.external_post_url && (
            <a
              href={item.external_post_url}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-emerald-600 hover:text-emerald-800 font-semibold px-2 py-1 bg-emerald-50 rounded"
            >
              Xem link ↗
            </a>
          )}
          {item.publish_status === 'PUBLISHED' && (
            <Button
              variant="outline"
              size="sm"
              disabled={syncingId === item.id}
              onClick={() => handleSyncMetrics(item.id)}
            >
              {syncingId === item.id ? 'Đang sync...' : '🔄 Sync'}
            </Button>
          )}
          {item.publish_status === 'FAILED' && (
            <Button
              variant="primary"
              size="sm"
              disabled={retryingId === item.id}
              onClick={() => handleRetryPost(item.id)}
              className="bg-amber-600 hover:bg-amber-700 text-white"
            >
              {retryingId === item.id ? 'Đang thử...' : '🔁 Thử lại'}
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Sub Tabs Bar */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-2 flex items-center justify-between shadow-2xs">
        <div className="flex gap-2">
          <button
            onClick={() => setActiveSubTab('CONNECTIONS')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 ${
              activeSubTab === 'CONNECTIONS'
                ? 'bg-emerald-600 text-white shadow-xs'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <span>🔗</span>
            <span>Kênh kết nối mạng xã hội ({connections.length})</span>
          </button>
          <button
            onClick={() => setActiveSubTab('LOGS')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 ${
              activeSubTab === 'LOGS'
                ? 'bg-emerald-600 text-white shadow-xs'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <span>📜</span>
            <span>Nhật ký xuất bản & Hàng đợi ({totalPosts})</span>
          </button>
        </div>

        {activeSubTab === 'LOGS' && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleRunWorker}
            disabled={isWorkerRunning}
            className="border-emerald-600 text-emerald-700 hover:bg-emerald-50 text-xs"
          >
            {isWorkerRunning ? 'Worker đang quét...' : '⚡ Kích hoạt Worker quét bài đến hạn'}
          </Button>
        )}
      </div>

      {/* Global Toast / Feedback */}
      {feedbackMsg && (
        <div
          className={`p-3.5 rounded-xl border text-xs flex items-center justify-between animate-in fade-in ${
            feedbackMsg.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}
        >
          <span className="font-medium">
            {feedbackMsg.type === 'success' ? '✓ ' : '✕ '}
            {feedbackMsg.text}
          </span>
          <button
            onClick={() => setFeedbackMsg(null)}
            className="text-slate-400 hover:text-slate-700 text-sm font-bold ml-4"
          >
            ×
          </button>
        </div>
      )}

      {/* =================================================================== */}
      {/* TAB 1: SOCIAL CONNECTIONS */}
      {/* =================================================================== */}
      {activeSubTab === 'CONNECTIONS' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-800">Tài khoản & Nền tảng kết nối API</h3>
              <p className="text-xs text-slate-500">
                Hệ thống tự động kích hoạt Mock Sandbox Provider cho môi trường phát triển & kiểm thử.
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={loadConnections}
              disabled={isLoadingConnections}
            >
              Làm mới
            </Button>
          </div>

          {isLoadingConnections ? (
            <div className="py-12 text-center text-slate-400 text-xs">
              <span className="inline-block animate-spin text-xl mb-2">🔄</span>
              <p>Đang tải danh sách kết nối...</p>
            </div>
          ) : connections.length === 0 ? (
            <EmptyState
              title="Chưa có kết nối mạng xã hội nào"
              description="Hệ thống sẽ tự động tạo kết nối Sandbox khi bạn xuất bản bài viết đầu tiên."
              actionText="Tải lại kết nối"
              onAction={loadConnections}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {connections.map((conn) => {
                const info = getPlatformIcon(conn.platform);
                return (
                  <div
                    key={conn.id}
                    className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-xs hover:shadow-sm transition space-y-4 flex flex-col justify-between"
                  >
                    <div>
                      {/* Platform Header */}
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-2.5">
                          <span className="text-2xl">{info.icon}</span>
                          <div>
                            <h4 className="font-bold text-xs text-slate-900 leading-tight">
                              {conn.account_name}
                            </h4>
                            <span className="text-[10px] text-slate-400 font-mono block">
                              ID: {conn.account_id}
                            </span>
                          </div>
                        </div>
                        {getStatusBadge(conn.status)}
                      </div>

                      {/* Details & Badges */}
                      <div className="mt-3 pt-3 border-t border-slate-100 space-y-1.5 text-xs">
                        <div className="flex items-center justify-between text-slate-600">
                          <span className="text-[11px] text-slate-400">Nền tảng:</span>
                          <span className="font-semibold text-slate-800">{info.name}</span>
                        </div>
                        <div className="flex items-center justify-between text-slate-600">
                          <span className="text-[11px] text-slate-400">Chế độ vận hành:</span>
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-purple-50 text-purple-700 border border-purple-200">
                            {conn.is_mock ? '🧪 Sandbox Mock' : '🚀 Live API'}
                          </span>
                        </div>
                        {conn.metadata_json?.followers_count && (
                          <div className="flex items-center justify-between text-slate-600">
                            <span className="text-[11px] text-slate-400">Người theo dõi:</span>
                            <span className="font-bold text-slate-800">
                              {conn.metadata_json.followers_count.toLocaleString()}
                            </span>
                          </div>
                        )}
                        {conn.token_expires_at && (
                          <div className="flex items-center justify-between text-slate-600">
                            <span className="text-[11px] text-slate-400">Hạn Access Token:</span>
                            <span className="text-[10px] font-medium text-slate-600">
                              {new Date(conn.token_expires_at).toLocaleDateString('vi-VN')}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={testingId === conn.id}
                        onClick={() => handleTestConnection(conn.id)}
                        className="text-[11px]"
                      >
                        {testingId === conn.id ? 'Đang test...' : '⚡ Test API'}
                      </Button>

                      <div className="flex items-center gap-1.5">
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={refreshingId === conn.id}
                          onClick={() => handleRefreshToken(conn.id)}
                          className="text-[11px]"
                        >
                          {refreshingId === conn.id ? 'Đang renew...' : '🔄 Token'}
                        </Button>

                        {conn.is_connected && (
                          <button
                            onClick={() => handleDisconnect(conn.id, conn.account_name)}
                            className="p-1.5 text-slate-400 hover:text-rose-600 rounded transition"
                            title="Ngắt kết nối"
                          >
                            🔌
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* =================================================================== */}
      {/* TAB 2: PUBLISHING LOGS & QUEUE */}
      {/* =================================================================== */}
      {activeSubTab === 'LOGS' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-800">Nhật ký xuất bản đa kênh & Telemetry</h3>
              <p className="text-xs text-slate-500">
                Toàn bộ lịch sử đẩy bài qua các Provider Adapter, phản hồi trạng thái mạng xã hội và số liệu tương tác.
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={loadPublishedPosts}
              disabled={isLoadingPosts}
            >
              Làm mới danh sách
            </Button>
          </div>

          <DataTable<PublishedPostItem>
            data={publishedPosts}
            columns={columns}
            keyExtractor={(row) => row.id}
            isLoading={isLoadingPosts}
            emptyTitle="Chưa có bài viết nào được xuất bản"
            emptyDescription="Các bài viết sau khi xuất bản qua Facebook, TikTok, Instagram, Zalo hoặc Website Blog sẽ xuất hiện ở đây."
          />
        </div>
      )}
    </div>
  );
};
