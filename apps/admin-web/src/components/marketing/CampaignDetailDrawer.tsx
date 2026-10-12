'use client';

import React, { useState, useEffect } from 'react';
import { Drawer, Button, Badge } from '@moc-healthy/ui';
import { CampaignDetailResponse } from '@moc-healthy/contracts';
import { campaignsApi } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';

export interface CampaignDetailDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  campaignId: string | null;
  onCampaignUpdated?: () => void;
  onEdit?: (campaign: CampaignDetailResponse) => void;
}

const formatVND = (amount: number) => {
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
    maximumFractionDigits: 0,
  }).format(amount);
};

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
    case 'ACTIVE':
      return <Badge variant="success">🟢 Đang chạy</Badge>;
    case 'READY_FOR_REVIEW':
      return <Badge variant="warning">⏳ Chờ duyệt</Badge>;
    case 'APPROVED':
      return <Badge variant="info">✅ Đã phê duyệt</Badge>;
    case 'DRAFT':
      return <Badge variant="neutral">📝 Bản nháp</Badge>;
    case 'PAUSED':
      return <Badge variant="warning">⏸️ Tạm dừng</Badge>;
    case 'COMPLETED':
      return <Badge variant="success">🏁 Đã hoàn tất</Badge>;
    case 'CANCELLED':
      return <Badge variant="danger">❌ Đã hủy</Badge>;
    default:
      return <Badge variant="neutral">{status}</Badge>;
  }
};

const getObjectiveBadge = (objective: string) => {
  switch (objective) {
    case 'CONVERSION':
      return <Badge variant="success">🎯 Tăng chuyển đổi</Badge>;
    case 'AWARENESS':
      return <Badge variant="info">📢 Nhận diện thương hiệu</Badge>;
    case 'CLEARANCE':
      return <Badge variant="warning">⚡ Xả kho cận hạn</Badge>;
    case 'LOYALTY':
      return <Badge variant="neutral">👑 Tri ân khách hàng</Badge>;
    case 'REENGAGEMENT':
      return <Badge variant="neutral">🔄 Tái kích hoạt</Badge>;
    default:
      return <Badge variant="neutral">{objective}</Badge>;
  }
};

const getChannelIcon = (channel: string) => {
  switch (channel) {
    case 'FACEBOOK':
      return '📘 Facebook Ads';
    case 'ZALO':
      return '💬 Zalo OA / ZNS';
    case 'TIKTOK':
      return '🎵 TikTok Ads';
    case 'INSTAGRAM':
      return '📷 Instagram';
    case 'SMS':
      return '📱 SMS Brandname';
    case 'EMAIL':
      return '✉️ Email Marketing';
    case 'WEBSITE_BANNER':
      return '🌐 Website Banner';
    default:
      return channel;
  }
};

export const CampaignDetailDrawer: React.FC<CampaignDetailDrawerProps> = ({
  isOpen,
  onClose,
  campaignId,
  onCampaignUpdated,
  onEdit,
}) => {
  const { hasPermission } = useAuth();
  const canCreate = hasPermission('campaign.create');
  const canApprove = hasPermission('campaign.approve');

  const [campaign, setCampaign] = useState<CampaignDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && campaignId) {
      loadDetail(campaignId);
    } else {
      setCampaign(null);
      setErrorMsg(null);
    }
  }, [isOpen, campaignId]);

  const loadDetail = async (id: string) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const data = await campaignsApi.get(id);
      setCampaign(data);
    } catch (err: any) {
      setErrorMsg(err.message || 'Không thể tải thông tin chiến dịch');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAction = async (actionFn: () => Promise<any>, successMsg?: string) => {
    setActionLoading(true);
    setErrorMsg(null);
    try {
      await actionFn();
      if (campaignId) await loadDetail(campaignId);
      if (onCampaignUpdated) onCampaignUpdated();
    } catch (err: any) {
      setErrorMsg(err.message || 'Thao tác không thành công');
    } finally {
      setActionLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <Drawer
      isOpen={isOpen}
      onClose={onClose}
      title={campaign ? `Chiến dịch: ${campaign.code}` : 'Chi tiết chiến dịch'}
      maxWidth="xl"
    >
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-20 space-y-3">
          <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-slate-500">Đang tải dữ liệu chiến dịch...</p>
        </div>
      ) : errorMsg && !campaign ? (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-sm">
          {errorMsg}
        </div>
      ) : campaign ? (
        <div className="space-y-6 pb-12">
          {errorMsg && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded text-rose-700 text-xs">
              {errorMsg}
            </div>
          )}

          {/* Header Card */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-5">
            <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
              <span className="font-mono text-xs font-semibold px-2 py-0.5 bg-slate-200 text-slate-800 rounded">
                {campaign.code}
              </span>
              <div className="flex items-center gap-2">
                {getObjectiveBadge(campaign.objective)}
                {getStatusBadge(campaign.status)}
              </div>
            </div>
            <h2 className="text-xl font-bold text-slate-900">{campaign.name}</h2>
            {campaign.notes && (
              <p className="text-sm text-slate-600 mt-2 italic bg-white p-2.5 rounded border border-slate-100">
                &ldquo;{campaign.notes}&rdquo;
              </p>
            )}

            <div className="grid grid-cols-2 gap-4 mt-4 text-xs text-slate-600 border-t border-slate-200 pt-3">
              <div>
                <span className="text-slate-400 block">Thời gian diễn ra:</span>
                <span className="font-medium text-slate-800">
                  {formatDate(campaign.start_at)} &rarr; {formatDate(campaign.end_at)}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block">Khách hàng mục tiêu:</span>
                <div className="flex flex-wrap gap-1 mt-0.5">
                  {campaign.target_audience && campaign.target_audience.length > 0 ? (
                    campaign.target_audience.map((aud) => (
                      <span key={aud} className="px-1.5 py-0.5 bg-emerald-50 text-emerald-800 font-medium rounded border border-emerald-200 text-[11px]">
                        {aud}
                      </span>
                    ))
                  ) : (
                    <span className="text-slate-400 italic">Toàn bộ khách hàng</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* KPI & Financial Overview */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
              Hiệu quả & Tài chính Chiến dịch
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-white border border-slate-200 rounded-lg p-3 shadow-xs">
                <span className="text-[11px] text-slate-500 block">Ngân sách phê duyệt</span>
                <span className="text-sm font-bold text-slate-900">{formatVND(campaign.budget)}</span>
              </div>
              <div className="bg-white border border-slate-200 rounded-lg p-3 shadow-xs">
                <span className="text-[11px] text-slate-500 block">Đã chi thực tế</span>
                <span className="text-sm font-bold text-amber-700">{formatVND(campaign.actual_spend)}</span>
              </div>
              <div className="bg-white border border-slate-200 rounded-lg p-3 shadow-xs">
                <span className="text-[11px] text-slate-500 block">Doanh thu ghi nhận</span>
                <span className="text-sm font-bold text-emerald-700">{formatVND(campaign.revenue_attributed)}</span>
              </div>
              <div className="bg-white border border-slate-200 rounded-lg p-3 shadow-xs">
                <span className="text-[11px] text-slate-500 block">Tỷ lệ ROI</span>
                <span
                  className={`text-sm font-extrabold ${
                    campaign.roi_percentage > 0
                      ? 'text-emerald-600'
                      : campaign.roi_percentage < 0
                      ? 'text-rose-600'
                      : 'text-slate-500'
                  }`}
                >
                  {campaign.roi_percentage > 0 ? `+${campaign.roi_percentage}%` : `${campaign.roi_percentage}%`}
                </span>
              </div>
            </div>
          </div>

          {/* Marketing Channels */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Kênh phân phối ({campaign.channels?.length || 0})
              </h3>
            </div>
            {campaign.channels && campaign.channels.length > 0 ? (
              <div className="space-y-2">
                {campaign.channels.map((ch) => (
                  <div
                    key={ch.id}
                    className="flex flex-col sm:flex-row sm:items-center justify-between p-3 bg-white border border-slate-200 rounded-lg text-xs gap-2"
                  >
                    <div>
                      <span className="font-semibold text-slate-800">{getChannelIcon(ch.channel)}</span>
                      {ch.target_metric && (
                        <span className="ml-2 text-slate-500 italic">KPI: {ch.target_metric}</span>
                      )}
                      {ch.notes && <p className="text-[11px] text-slate-400 mt-0.5">{ch.notes}</p>}
                    </div>
                    <div className="flex items-center gap-3 text-right">
                      <div>
                        <span className="text-slate-400 block text-[10px]">Ngân sách</span>
                        <span className="font-medium text-slate-700">{formatVND(ch.channel_budget)}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px]">Đã chi</span>
                        <span className="font-medium text-amber-700">{formatVND(ch.channel_spend)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-center text-xs text-slate-500">
                Chưa gắn kênh phân phối nào cho chiến dịch này.
              </div>
            )}
          </div>

          {/* Hero Products */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
              Sản phẩm trọng tâm ({campaign.products?.length || 0})
            </h3>
            {campaign.products && campaign.products.length > 0 ? (
              <div className="space-y-2">
                {campaign.products.map((pr) => (
                  <div
                    key={pr.id}
                    className="flex items-center justify-between p-2.5 bg-white border border-slate-200 rounded-lg text-xs"
                  >
                    <div className="flex items-center gap-2">
                      {pr.is_hero_product && (
                        <span className="px-1.5 py-0.5 bg-amber-100 text-amber-800 font-bold rounded text-[10px]">
                          ⭐ HERO
                        </span>
                      )}
                      <span className="font-medium text-slate-800">{pr.product_name}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-slate-400 line-through">{formatVND(pr.product_price)}</span>
                      <span className="font-bold text-emerald-700">
                        {pr.special_price ? formatVND(pr.special_price) : formatVND(pr.product_price)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-center text-xs text-slate-500">
                Áp dụng toàn bộ menu sản phẩm hoặc chưa chọn sản phẩm hero.
              </div>
            )}
          </div>

          {/* Promotion & Tracking Info */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
              Khuyến mãi & Mã theo dõi (UTM)
            </h3>
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs space-y-2">
              {campaign.promotion_name && (
                <div className="flex justify-between items-center py-1 border-b border-slate-200">
                  <span className="text-slate-500">Ưu đãi liên kết:</span>
                  <span className="font-semibold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    🎁 {campaign.promotion_name}
                  </span>
                </div>
              )}
              {campaign.landing_page && (
                <div className="flex justify-between items-center py-1 border-b border-slate-200">
                  <span className="text-slate-500">Landing Page:</span>
                  <a
                    href={campaign.landing_page}
                    target="_blank"
                    rel="noreferrer"
                    className="text-emerald-700 hover:underline font-mono truncate max-w-[260px]"
                  >
                    {campaign.landing_page}
                  </a>
                </div>
              )}
              <div className="grid grid-cols-3 gap-2 pt-1 font-mono text-[11px]">
                <div>
                  <span className="text-slate-400 block font-sans text-[10px]">utm_source</span>
                  <span className="text-slate-700 font-semibold">{campaign.utm_source || '---'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block font-sans text-[10px]">utm_medium</span>
                  <span className="text-slate-700 font-semibold">{campaign.utm_medium || '---'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block font-sans text-[10px]">utm_campaign</span>
                  <span className="text-slate-700 font-semibold">{campaign.utm_campaign || '---'}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Audit trail */}
          <div className="text-[11px] text-slate-400 border-t border-slate-200 pt-3 space-y-1">
            <div>
              <span>Người tạo: </span>
              <span className="text-slate-600 font-medium">{campaign.created_by_user_name || 'Hệ thống'}</span>
              <span> vào lúc {formatDate(campaign.created_at)}</span>
            </div>
            {campaign.approved_at && (
              <div>
                <span>Phê duyệt bởi: </span>
                <span className="text-slate-600 font-medium">{campaign.approved_by_user_name || 'Quản lý'}</span>
                <span> vào lúc {formatDate(campaign.approved_at)}</span>
              </div>
            )}
          </div>

          {/* Action buttons bar */}
          <div className="border-t border-slate-200 pt-4 flex flex-wrap gap-2 justify-end">
            {campaign.status === 'DRAFT' && canCreate && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onEdit && onEdit(campaign)}
                  disabled={actionLoading}
                >
                  ✏️ Chỉnh sửa
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  disabled={actionLoading}
                  onClick={() => handleAction(() => campaignsApi.submitReview(campaign.id))}
                >
                  📨 Gửi duyệt chiến dịch
                </Button>
              </>
            )}

            {campaign.status === 'READY_FOR_REVIEW' && canApprove && (
              <Button
                variant="primary"
                size="sm"
                className="bg-emerald-600 hover:bg-emerald-700"
                disabled={actionLoading}
                onClick={() => handleAction(() => campaignsApi.approve(campaign.id))}
              >
                ✅ Phê duyệt chiến dịch
              </Button>
            )}

            {campaign.status === 'APPROVED' && canCreate && (
              <Button
                variant="primary"
                size="sm"
                className="bg-emerald-600 hover:bg-emerald-700"
                disabled={actionLoading}
                onClick={() => handleAction(() => campaignsApi.updateStatus(campaign.id, 'ACTIVE'))}
              >
                🚀 Bắt đầu chiến dịch (Activate)
              </Button>
            )}

            {campaign.status === 'ACTIVE' && canCreate && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={actionLoading}
                  onClick={() => handleAction(() => campaignsApi.updateStatus(campaign.id, 'PAUSED'))}
                >
                  ⏸️ Tạm dừng
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  disabled={actionLoading}
                  onClick={() => handleAction(() => campaignsApi.updateStatus(campaign.id, 'COMPLETED'))}
                >
                  🏁 Kết thúc & Hoàn tất
                </Button>
              </>
            )}

            {campaign.status === 'PAUSED' && canCreate && (
              <>
                <Button
                  variant="primary"
                  size="sm"
                  disabled={actionLoading}
                  onClick={() => handleAction(() => campaignsApi.updateStatus(campaign.id, 'ACTIVE'))}
                >
                  ▶️ Tiếp tục chạy
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={actionLoading}
                  onClick={() => handleAction(() => campaignsApi.updateStatus(campaign.id, 'COMPLETED'))}
                >
                  🏁 Hoàn tất
                </Button>
              </>
            )}

            {['DRAFT', 'READY_FOR_REVIEW', 'APPROVED', 'PAUSED'].includes(campaign.status) && canCreate && (
              <Button
                variant="danger"
                size="sm"
                disabled={actionLoading}
                onClick={() => handleAction(() => campaignsApi.updateStatus(campaign.id, 'CANCELLED'))}
              >
                Hủy bỏ
              </Button>
            )}
          </div>
        </div>
      ) : null}
    </Drawer>
  );
};
