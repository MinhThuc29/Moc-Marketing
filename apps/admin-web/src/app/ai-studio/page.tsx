'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { AdminShell } from '../../components/shell/AdminShell';
import { PageHeader } from '../../components/shell/PageHeader';
import { Button, Input, Select, Badge, Card, StatCard, EmptyState } from '@moc-healthy/ui';
import {
  AIGeneratedVariant,
  AIGenerateResponse,
  ContentType,
  ContentChannel,
  BrandTone,
  AIRecommendationItem,
  RecommendationOverviewStats,
  SmartAlertItem,
} from '@moc-healthy/contracts';
import {
  contentApi,
  productsApi,
  campaignsApi,
  recommendationsApi,
  alertsApi,
} from '../../lib/api';
import { RecommendationCard } from '../../components/recommendations/RecommendationCard';
import { SmartAlertsBanner } from '../../components/recommendations/SmartAlertsBanner';

const AVAILABLE_CHANNELS = [
  { value: 'FACEBOOK', label: '📘 Facebook Fanpage' },
  { value: 'INSTAGRAM', label: '📷 Instagram Feed & Reel' },
  { value: 'TIKTOK', label: '🎵 TikTok Short Video' },
  { value: 'ZALO', label: '💬 Zalo OA / ZNS' },
  { value: 'WEBSITE_BANNER', label: '🌐 Website Banner Copy' },
];

const AVAILABLE_TYPES = [
  { value: 'FACEBOOK_POST', label: 'Bài viết Facebook (AIDA / PAS Model)' },
  { value: 'TIKTOK_SCRIPT', label: 'Kịch bản TikTok 45s (Kèm Storyboard phân cảnh)' },
  { value: 'REEL_SCRIPT', label: 'Kịch bản Instagram Reel 30s' },
  { value: 'ZALO_MESSAGE', label: 'Tin nhắn CSKH Zalo OA' },
  { value: 'WEBSITE_BANNER_COPY', label: 'Tiêu đề Banner & CTA Website' },
  { value: 'PRODUCT_STORY', label: 'Câu chuyện sản phẩm (Storytelling)' },
  { value: 'SEO_ARTICLE', label: 'Bài viết ngắn chuẩn SEO' },
];

const AVAILABLE_TONES = [
  { value: 'FRESH_ENERGETIC', label: '🌱 Tươi mới, tràn đầy năng lượng' },
  { value: 'NUTRITION_EXPERT', label: '🔬 Chuyên gia dinh dưỡng tin cậy' },
  { value: 'WARM_FRIENDLY', label: '💖 Gần gũi, ấm áp, chăm sóc' },
  { value: 'MINIMAL_HEALTHY', label: '🧘 Tối giản, thanh lọc cơ thể' },
  { value: 'TRENDY_HUMOR', label: '⚡ Trẻ trung, bắt trend, hài hước' },
];

const QUICK_PROMPT_PRESETS = [
  {
    label: '🎯 Bữa trưa văn phòng',
    text: 'Tập trung vào đối tượng dân công sở bận rộn, muốn ăn sạch healthy không lo tăng cân hay buồn ngủ buổi chiều.',
  },
  {
    label: '⚡ Flash Sale cuối tuần',
    text: 'Thúc đẩy mua ngay trong 48h tới, tặng kèm quà tặng cho đơn từ 299k, số lượng có hạn.',
  },
  {
    label: '🌿 100% Thuần khiết',
    text: 'Nhấn mạnh nguồn gốc nguyên liệu đạt chuẩn, không chất bảo quản, không đường hóa học, an toàn cho mẹ bầu và trẻ nhỏ.',
  },
  {
    label: '🥑 Hướng dẫn kết hợp',
    text: 'Gợi ý cách mix đồ ăn sáng cùng sữa chua Hy Lạp hoặc smoothie bowl cho người tập gym, giảm mỡ.',
  },
];

export default function AIStudioPage() {
  const router = useRouter();

  // Primary Tab: 'RECOMMENDATIONS' or 'CONTENT_STUDIO'
  const [activeMainTab, setActiveMainTab] = useState<'RECOMMENDATIONS' | 'CONTENT_STUDIO'>('RECOMMENDATIONS');

  // =========================================================================
  // STATE: AI RECOMMENDATIONS & SMART ALERTS
  // =========================================================================
  const [recommendations, setRecommendations] = useState<AIRecommendationItem[]>([]);
  const [recStats, setRecStats] = useState<RecommendationOverviewStats | null>(null);
  const [alerts, setAlerts] = useState<SmartAlertItem[]>([]);
  const [isRecLoading, setIsRecLoading] = useState<boolean>(true);
  const [isScanningRecs, setIsScanningRecs] = useState<boolean>(false);
  const [isScanningAlerts, setIsScanningAlerts] = useState<boolean>(false);

  // Filters for Recommendations
  const [recTypeFilter, setRecTypeFilter] = useState<string>('');
  const [recConfidenceFilter, setRecConfidenceFilter] = useState<string>('');
  const [recStatusFilter, setRecStatusFilter] = useState<string>('PENDING');

  // Action Modals State
  const [selectedRecForCampaign, setSelectedRecForCampaign] = useState<AIRecommendationItem | null>(null);
  const [campaignCustomName, setCampaignCustomName] = useState<string>('');
  const [campaignBudget, setCampaignBudget] = useState<number>(1000000);
  const [isConvertingCampaign, setIsConvertingCampaign] = useState<boolean>(false);

  const [selectedRecForDismiss, setSelectedRecForDismiss] = useState<AIRecommendationItem | null>(null);
  const [dismissReason, setDismissReason] = useState<string>('');
  const [isDismissing, setIsDismissing] = useState<boolean>(false);

  const [feedbackMsg, setFeedbackMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // =========================================================================
  // STATE: CONTENT STUDIO GENERATOR (EXISTING)
  // =========================================================================
  const [selectedProductId, setSelectedProductId] = useState<string>('');
  const [selectedCampaignId, setSelectedCampaignId] = useState<string>('');
  const [channel, setChannel] = useState<ContentChannel>('FACEBOOK');
  const [contentType, setContentType] = useState<ContentType>('FACEBOOK_POST');
  const [brandTone, setBrandTone] = useState<BrandTone>('FRESH_ENERGETIC');
  const [numVariants, setNumVariants] = useState<number>(2);
  const [customInstruction, setCustomInstruction] = useState<string>('');

  const [productsList, setProductsList] = useState<Array<{ id: string; name: string }>>([]);
  const [campaignsList, setCampaignsList] = useState<Array<{ id: string; name: string }>>([]);
  const [loadingDependencies, setLoadingDependencies] = useState<boolean>(true);

  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [generationResult, setGenerationResult] = useState<AIGenerateResponse | null>(null);
  const [activeVariantIndex, setActiveVariantIndex] = useState<number>(0);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [savingIndex, setSavingIndex] = useState<number | null>(null);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  // Load initial data
  useEffect(() => {
    loadRecommendationsData();
    loadDependencies();
  }, []);

  const loadRecommendationsData = async () => {
    setIsRecLoading(true);
    try {
      const [overviewRes, recsRes, alertsRes] = await Promise.all([
        recommendationsApi.getOverview(),
        recommendationsApi.list({
          status: recStatusFilter || undefined,
          type: recTypeFilter || undefined,
          confidence: recConfidenceFilter || undefined,
          limit: 30,
        }),
        alertsApi.list({ status: 'ACTIVE', limit: 10 }),
      ]);
      setRecStats(overviewRes);
      setRecommendations(recsRes.items);
      setAlerts(alertsRes.items);
    } catch (err: any) {
      console.error('Lỗi tải dữ liệu recommendations/alerts:', err);
    } finally {
      setIsRecLoading(false);
    }
  };

  const handleFilterChange = useCallback(async () => {
    setIsRecLoading(true);
    try {
      const recsRes = await recommendationsApi.list({
        status: recStatusFilter || undefined,
        type: recTypeFilter || undefined,
        confidence: recConfidenceFilter || undefined,
        limit: 30,
      });
      setRecommendations(recsRes.items);
    } catch (err) {
      console.error(err);
    } finally {
      setIsRecLoading(false);
    }
  }, [recStatusFilter, recTypeFilter, recConfidenceFilter]);

  useEffect(() => {
    handleFilterChange();
  }, [recStatusFilter, recTypeFilter, recConfidenceFilter, handleFilterChange]);

  const loadDependencies = async () => {
    setLoadingDependencies(true);
    try {
      const [prodsRes, campsRes] = await Promise.all([
        productsApi.list({ page_size: 50 }),
        campaignsApi.list({ page_size: 50 }),
      ]);
      setProductsList(prodsRes.items.map((p) => ({ id: p.id, name: p.name })));
      setCampaignsList(campsRes.items.map((c) => ({ id: c.id, name: c.name })));
    } catch (err: any) {
      console.error('Lỗi tải danh mục sản phẩm/chiến dịch:', err);
    } finally {
      setLoadingDependencies(false);
    }
  };

  // =========================================================================
  // HANDLERS: RECOMMENDATIONS & ALERTS
  // =========================================================================
  const handleScanRecommendations = async () => {
    setIsScanningRecs(true);
    setFeedbackMsg(null);
    try {
      const newRecs = await recommendationsApi.generate({ force_regenerate: true });
      setFeedbackMsg({
        type: 'success',
        text: `Đã hoàn tất phân tích toàn hệ thống! Cập nhật ${newRecs.length} khuyến nghị kinh doanh dựa trên bằng chứng dữ liệu thực tế.`,
      });
      await loadRecommendationsData();
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: err.message || 'Lỗi khi quét và sinh đề xuất AI.' });
    } finally {
      setIsScanningRecs(false);
    }
  };

  const handleConfirmConvertToCampaign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRecForCampaign) return;
    setIsConvertingCampaign(true);
    try {
      const res = await recommendationsApi.convertToCampaign(selectedRecForCampaign.id, {
        custom_name: campaignCustomName.trim() || undefined,
        budget: Number(campaignBudget) || undefined,
      });
      setFeedbackMsg({
        type: 'success',
        text: `🚀 ${res.message} Mã chiến dịch: ${res.campaign_code}.`,
      });
      setSelectedRecForCampaign(null);
      await loadRecommendationsData();
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: err.message || 'Lỗi khi chuyển đổi sang chiến dịch.' });
    } finally {
      setIsConvertingCampaign(false);
    }
  };

  const handleConvertToAutomation = async (rec: AIRecommendationItem) => {
    if (!confirm(`Xác nhận tạo Kịch bản Tự động hóa tiếp thị từ đề xuất: "${rec.title}"?`)) return;
    try {
      const res = await recommendationsApi.convertToAutomation(rec.id);
      setFeedbackMsg({
        type: 'success',
        text: `⚡ ${res.message} Mã workflow: ${res.workflow_code}.`,
      });
      await loadRecommendationsData();
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: err.message || 'Lỗi khi tạo workflow tự động hóa.' });
    }
  };

  const handleConfirmDismiss = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRecForDismiss) return;
    setIsDismissing(true);
    try {
      await recommendationsApi.dismiss(selectedRecForDismiss.id, {
        reason: dismissReason.trim() || undefined,
      });
      setFeedbackMsg({
        type: 'success',
        text: `Đã đánh dấu bỏ qua đề xuất "${selectedRecForDismiss.title}".`,
      });
      setSelectedRecForDismiss(null);
      setDismissReason('');
      await loadRecommendationsData();
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: err.message || 'Lỗi khi bỏ qua đề xuất.' });
    } finally {
      setIsDismissing(false);
    }
  };

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      await alertsApi.acknowledge(alertId);
      setAlerts((prev) => prev.map((a) => (a.id === alertId ? { ...a, status: 'ACKNOWLEDGED' } : a)));
    } catch (err) {
      console.error(err);
    }
  };

  const handleResolveAlert = async (alertId: string) => {
    try {
      await alertsApi.resolve(alertId);
      setAlerts((prev) => prev.filter((a) => a.id !== alertId));
      if (recStats) {
        setRecStats({ ...recStats, active_alerts_count: Math.max(0, recStats.active_alerts_count - 1) });
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleScanAlerts = async () => {
    setIsScanningAlerts(true);
    try {
      const newAlerts = await alertsApi.scan();
      setAlerts(newAlerts);
      await loadRecommendationsData();
    } catch (err) {
      console.error(err);
    } finally {
      setIsScanningAlerts(false);
    }
  };

  // =========================================================================
  // HANDLERS: CONTENT STUDIO (EXISTING)
  // =========================================================================
  const handleChannelChange = (newChannel: ContentChannel) => {
    setChannel(newChannel);
    if (newChannel === 'TIKTOK') setContentType('TIKTOK_SCRIPT');
    else if (newChannel === 'INSTAGRAM') setContentType('REEL_SCRIPT');
    else if (newChannel === 'ZALO') setContentType('ZALO_MESSAGE');
    else if (newChannel === 'WEBSITE_BANNER') setContentType('WEBSITE_BANNER_COPY');
    else setContentType('FACEBOOK_POST');
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsGenerating(true);
    setErrorMsg(null);
    setSaveSuccessMsg(null);

    try {
      const res = await contentApi.generateAI({
        product_id: selectedProductId || null,
        campaign_id: selectedCampaignId || null,
        channel: channel,
        content_type: contentType,
        brand_tone: brandTone,
        custom_instruction: customInstruction.trim() || null,
        num_variants: numVariants,
      });

      setGenerationResult(res);
      setActiveVariantIndex(0);
    } catch (err: any) {
      setErrorMsg(err.message || 'Không thể sinh nội dung. Vui lòng thử lại sau.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSaveToLibrary = async (variant: AIGeneratedVariant, index: number) => {
    setSavingIndex(index);
    setSaveSuccessMsg(null);
    setErrorMsg(null);

    try {
      const res = await contentApi.create({
        title: variant.title,
        channel: channel,
        content_type: contentType,
        body: variant.body,
        hook: variant.hook,
        cta: variant.cta,
        hashtags: variant.hashtags,
        product_id: selectedProductId || undefined,
        campaign_id: selectedCampaignId || undefined,
      });

      setSaveSuccessMsg(`Đã lưu bài viết "${res.title}" vào Kho nội dung thành công!`);
    } catch (err: any) {
      setErrorMsg(err.message || 'Không thể lưu bài viết.');
    } finally {
      setSavingIndex(null);
    }
  };

  const handleCopyText = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const currentVariant = generationResult?.variants[activeVariantIndex];

  return (
    <AdminShell requiredPermission="content.create">
      <PageHeader
        title="06 AI Studio"
        subtitle="Trung tâm Trí tuệ Nhân tạo Mộc Healthy: Chiến lược gia kinh doanh AI (Evidence-based) & Sáng tạo nội dung đa kênh."
        breadcrumbs={[
          { label: 'Admin Hub', href: '/' },
          { label: 'AI Studio' },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <Link href="/content">
              <Button variant="outline" size="sm">
                📁 Quản lý kho nội dung
              </Button>
            </Link>
            <Link href="/marketing">
              <Button variant="outline" size="sm">
                🎯 Chiến dịch tiếp thị
              </Button>
            </Link>
          </div>
        }
      />

      {/* PRIMARY TAB NAVIGATION */}
      <div className="flex border-b border-slate-200 mb-6 gap-2">
        <button
          onClick={() => setActiveMainTab('RECOMMENDATIONS')}
          className={`px-4 py-2.5 font-bold text-sm border-b-2 flex items-center gap-2 transition ${
            activeMainTab === 'RECOMMENDATIONS'
              ? 'border-emerald-600 text-emerald-700 bg-emerald-50/50 rounded-t-lg'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <span>💡</span>
          <span>Đề xuất thông minh & Cảnh báo (AI Strategist)</span>
          {recStats?.pending_count ? (
            <span className="bg-emerald-100 text-emerald-800 text-xs px-2 py-0.5 rounded-full font-bold">
              {recStats.pending_count}
            </span>
          ) : null}
        </button>
        <button
          onClick={() => setActiveMainTab('CONTENT_STUDIO')}
          className={`px-4 py-2.5 font-bold text-sm border-b-2 flex items-center gap-2 transition ${
            activeMainTab === 'CONTENT_STUDIO'
              ? 'border-emerald-600 text-emerald-700 bg-emerald-50/50 rounded-t-lg'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <span>✍️</span>
          <span>AI Content Studio (Tạo bài viết & Video)</span>
        </button>
      </div>

      {feedbackMsg && (
        <div
          className={`mb-6 p-4 rounded-xl flex items-center justify-between text-sm ${
            feedbackMsg.type === 'success'
              ? 'bg-emerald-50 border border-emerald-200 text-emerald-800'
              : 'bg-rose-50 border border-rose-200 text-rose-800'
          }`}
        >
          <div className="flex items-center gap-2">
            <span>{feedbackMsg.type === 'success' ? '🎉' : '⚠️'}</span>
            <span>{feedbackMsg.text}</span>
          </div>
          <button
            onClick={() => setFeedbackMsg(null)}
            className="text-xs font-semibold underline hover:opacity-80 ml-4"
          >
            Đóng
          </button>
        </div>
      )}

      {/* =================================================================== */}
      {/* TAB 1: AI RECOMMENDATIONS & SMART ALERTS                            */}
      {/* =================================================================== */}
      {activeMainTab === 'RECOMMENDATIONS' && (
        <div className="space-y-6">
          {/* Executive Stat Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Đề xuất chờ duyệt"
              value={recStats?.pending_count ?? 0}
              change="Cần quyết định kinh doanh"
              icon="💡"
            />
            <StatCard
              title="Độ tin cậy cao (>80%)"
              value={recStats?.high_confidence_count ?? 0}
              change="Chứng cứ xác thực từ DB"
              changeType="positive"
              icon="🎯"
            />
            <StatCard
              title="Đã áp dụng chuyển đổi"
              value={recStats?.applied_count ?? 0}
              change="Thành Campaign / Workflow"
              icon="🚀"
            />
            <StatCard
              title="Cảnh báo vận hành"
              value={recStats?.active_alerts_count ?? 0}
              change={`${recStats?.critical_alerts_count ?? 0} cảnh báo khẩn cấp`}
              changeType={recStats?.critical_alerts_count ? 'negative' : 'neutral'}
              icon="🚨"
            />
          </div>

          {/* Smart Alerts Banner */}
          <SmartAlertsBanner
            alerts={alerts}
            onAcknowledge={handleAcknowledgeAlert}
            onResolve={handleResolveAlert}
            onRefresh={handleScanAlerts}
            isScanning={isScanningAlerts}
          />

          {/* Filter Bar & Scan Action */}
          <div className="bg-white p-4 rounded-xl border border-slate-200 flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-3">
              <div className="w-48">
                <Select
                  value={recTypeFilter}
                  onChange={(e) => setRecTypeFilter(e.target.value)}
                  options={[
                    { value: '', label: 'Tất cả loại đề xuất' },
                    { value: 'INVENTORY_CLEARANCE', label: '📦 Xả kho cận date' },
                    { value: 'CAMPAIGN_OPPORTUNITY', label: '🚀 Cơ hội chiến dịch' },
                    { value: 'CUSTOMER_RETENTION', label: '👥 Giữ chân khách hàng' },
                    { value: 'CHANNEL_OPTIMIZATION', label: '⚡ Tối ưu kênh sàn' },
                  ]}
                />
              </div>

              <div className="w-40">
                <Select
                  value={recConfidenceFilter}
                  onChange={(e) => setRecConfidenceFilter(e.target.value)}
                  options={[
                    { value: '', label: 'Tất cả độ tin cậy' },
                    { value: 'HIGH', label: '🟢 Độ tin cậy cao' },
                    { value: 'MEDIUM', label: '🟡 Độ tin cậy vừa' },
                    { value: 'LOW', label: '⚪ Thấp / Khảo sát' },
                  ]}
                />
              </div>

              <div className="w-36">
                <Select
                  value={recStatusFilter}
                  onChange={(e) => setRecStatusFilter(e.target.value)}
                  options={[
                    { value: '', label: 'Tất cả trạng thái' },
                    { value: 'PENDING', label: '⏳ Chờ duyệt' },
                    { value: 'APPLIED', label: '✅ Đã áp dụng' },
                    { value: 'DISMISSED', label: '🚫 Đã bỏ qua' },
                  ]}
                />
              </div>
            </div>

            <Button
              variant="primary"
              size="sm"
              onClick={handleScanRecommendations}
              disabled={isScanningRecs}
              className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold flex items-center gap-1.5"
            >
              <span>{isScanningRecs ? '⏳' : '🔍'}</span>
              <span>{isScanningRecs ? 'Đang phân tích dữ liệu...' : 'Quét dữ liệu & Sinh đề xuất mới'}</span>
            </Button>
          </div>

          {/* Recommendations List */}
          {isRecLoading ? (
            <div className="py-12 text-center text-slate-400">
              <span className="inline-block animate-spin text-2xl mb-2">🔄</span>
              <p className="text-sm">Đang tải các đề xuất chiến lược AI...</p>
            </div>
          ) : recommendations.length === 0 ? (
            <EmptyState
              title="Không có đề xuất nào phù hợp"
              description="Hiện tại không có khuyến nghị nào theo bộ lọc đang chọn. Nhấn 'Quét dữ liệu' để AI phân tích lại hệ thống."
              actionText="Quét dữ liệu ngay"
              onAction={handleScanRecommendations}
            />
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              {recommendations.map((rec) => (
                <RecommendationCard
                  key={rec.id}
                  recommendation={rec}
                  onConvertToCampaign={(r) => {
                    setSelectedRecForCampaign(r);
                    setCampaignCustomName(`[AI] ${r.title}`);
                    setCampaignBudget(r.expected_impact?.estimated_revenue ? Math.round(r.expected_impact.estimated_revenue * 0.3) : 1000000);
                  }}
                  onConvertToAutomation={handleConvertToAutomation}
                  onDismiss={(r) => setSelectedRecForDismiss(r)}
                />
              ))}
            </div>
          )}

          {/* Modal: Convert to Campaign */}
          {selectedRecForCampaign && (
            <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
              <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 animate-in fade-in zoom-in-95">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <h3 className="text-base font-bold text-slate-900">
                    🚀 1-Click: Tạo Chiến Dịch Tiếp Thị
                  </h3>
                  <button
                    onClick={() => setSelectedRecForCampaign(null)}
                    className="text-slate-400 hover:text-slate-600"
                  >
                    ✕
                  </button>
                </div>

                <form onSubmit={handleConfirmConvertToCampaign} className="mt-4 space-y-4">
                  <p className="text-xs text-slate-600">
                    Chuyển đổi khuyến nghị <strong className="text-slate-800">"{selectedRecForCampaign.title}"</strong> thành bản nháp chiến dịch tiếp thị trong Campaign Hub.
                  </p>

                  <Input
                    label="Tên chiến dịch"
                    value={campaignCustomName}
                    onChange={(e) => setCampaignCustomName(e.target.value)}
                    required
                  />

                  <Input
                    label="Ngân sách dự kiến (VND)"
                    type="number"
                    value={String(campaignBudget)}
                    onChange={(e) => setCampaignBudget(Number(e.target.value))}
                    required
                  />

                  <div className="p-3 bg-emerald-50 rounded-lg text-xs text-emerald-800 space-y-1">
                    <p className="font-semibold">Kênh áp dụng tự động:</p>
                    <p>{selectedRecForCampaign.target_channels.join(', ') || 'Website Banner'}</p>
                  </div>

                  <div className="pt-2 flex items-center justify-end gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedRecForCampaign(null)}
                      type="button"
                    >
                      Hủy bỏ
                    </Button>
                    <Button
                      variant="primary"
                      size="sm"
                      type="submit"
                      disabled={isConvertingCampaign}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white"
                    >
                      {isConvertingCampaign ? 'Đang tạo...' : 'Xác nhận tạo Chiến dịch'}
                    </Button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {/* Modal: Dismiss Recommendation */}
          {selectedRecForDismiss && (
            <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
              <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 animate-in fade-in zoom-in-95">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <h3 className="text-base font-bold text-slate-900">
                    Bỏ qua khuyến nghị này
                  </h3>
                  <button
                    onClick={() => setSelectedRecForDismiss(null)}
                    className="text-slate-400 hover:text-slate-600"
                  >
                    ✕
                  </button>
                </div>

                <form onSubmit={handleConfirmDismiss} className="mt-4 space-y-4">
                  <p className="text-xs text-slate-600">
                    Bạn muốn bỏ qua đề xuất <strong className="text-slate-800">"{selectedRecForDismiss.title}"</strong>?
                  </p>

                  <Input
                    label="Lý do bỏ qua (Tùy chọn)"
                    placeholder="VD: Không đủ nhân sự, Đã có kế hoạch khác..."
                    value={dismissReason}
                    onChange={(e) => setDismissReason(e.target.value)}
                  />

                  <div className="pt-2 flex items-center justify-end gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedRecForDismiss(null)}
                      type="button"
                    >
                      Quay lại
                    </Button>
                    <Button
                      variant="danger"
                      size="sm"
                      type="submit"
                      disabled={isDismissing}
                    >
                      {isDismissing ? 'Đang xử lý...' : 'Xác nhận bỏ qua'}
                    </Button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      )}

      {/* =================================================================== */}
      {/* TAB 2: AI CONTENT STUDIO (GENERATOR & STORYBOARD)                   */}
      {/* =================================================================== */}
      {activeMainTab === 'CONTENT_STUDIO' && (
        <>
          {saveSuccessMsg && (
            <div className="mb-6 p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between text-emerald-800 text-sm">
              <div className="flex items-center gap-2">
                <span className="text-xl">🎉</span>
                <span>{saveSuccessMsg}</span>
              </div>
              <Link href="/content">
                <Button variant="primary" size="sm">
                  Xem trong Kho nội dung →
                </Button>
              </Link>
            </div>
          )}

          {errorMsg && (
            <div className="mb-6 p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-center justify-between text-rose-800 text-sm">
              <div className="flex items-center gap-2">
                <span className="text-xl">⚠️</span>
                <span>{errorMsg}</span>
              </div>
              <button
                onClick={() => setErrorMsg(null)}
                className="text-rose-500 hover:text-rose-700 text-xs font-semibold"
              >
                Đóng
              </button>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* CỘT TRÁI: FORM CẤU HÌNH SINH NỘI DUNG (5 Cột) */}
            <div className="lg:col-span-5 space-y-6">
              <Card title="⚙️ Tham số sáng tạo AI" className="shadow-xs">
                <form onSubmit={handleGenerate} className="space-y-4">
                  {/* Chọn sản phẩm */}
                  <div>
                    <Select
                      label="Sản phẩm mục tiêu (Tùy chọn)"
                      value={selectedProductId}
                      onChange={(e) => setSelectedProductId(e.target.value)}
                      disabled={loadingDependencies}
                      options={[
                        { value: '', label: '--- Chọn sản phẩm từ Menu ---' },
                        ...productsList.map((p) => ({ value: p.id, label: p.name })),
                      ]}
                    />
                    <p className="text-[11px] text-slate-400 mt-1">
                      AI sẽ tự động đọc giá, thành phần, công dụng và hạn dùng từ DB.
                    </p>
                  </div>

                  {/* Chọn chiến dịch */}
                  <div>
                    <Select
                      label="Chiến dịch liên kết (Tùy chọn)"
                      value={selectedCampaignId}
                      onChange={(e) => setSelectedCampaignId(e.target.value)}
                      disabled={loadingDependencies}
                      options={[
                        { value: '', label: '--- Chọn chiến dịch liên quan ---' },
                        ...campaignsList.map((c) => ({ value: c.id, label: c.name })),
                      ]}
                    />
                  </div>

                  {/* Kênh phát hành */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                      Kênh phát hành mục tiêu
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {AVAILABLE_CHANNELS.map((ch) => (
                        <button
                          key={ch.value}
                          type="button"
                          onClick={() => handleChannelChange(ch.value as ContentChannel)}
                          className={`p-2.5 rounded-lg border text-xs font-medium text-left transition ${
                            channel === ch.value
                              ? 'border-emerald-600 bg-emerald-50/50 text-emerald-800 font-bold'
                              : 'border-slate-200 text-slate-700 hover:border-slate-300'
                          }`}
                        >
                          {ch.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Định dạng nội dung */}
                  <div>
                    <Select
                      label="Định dạng bài đăng / Kịch bản"
                      value={contentType}
                      onChange={(e) => setContentType(e.target.value as ContentType)}
                      options={AVAILABLE_TYPES}
                    />
                  </div>

                  {/* Giọng điệu thương hiệu */}
                  <div>
                    <Select
                      label="Giọng điệu thương hiệu (Brand Tone)"
                      value={brandTone}
                      onChange={(e) => setBrandTone(e.target.value as BrandTone)}
                      options={AVAILABLE_TONES}
                    />
                  </div>

                  {/* Số lượng biến thể */}
                  <div>
                    <Select
                      label="Số lượng biến thể đề xuất"
                      value={String(numVariants)}
                      onChange={(e) => setNumVariants(Number(e.target.value))}
                      options={[
                        { value: '1', label: '1 biến thể tập trung' },
                        { value: '2', label: '2 biến thể (So sánh A/B)' },
                        { value: '3', label: '3 biến thể đa dạng góc tiếp cận' },
                      ]}
                    />
                  </div>

                  {/* Hướng dẫn thêm */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                      Yêu cầu tùy biến bổ sung (Prompt)
                    </label>
                    <textarea
                      rows={3}
                      className="w-full text-xs p-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500 font-sans"
                      placeholder="VD: Nhấn mạnh vào lợi ích thanh lọc cơ thể sau Tết, kêu gọi mua combo 3 tặng 1..."
                      value={customInstruction}
                      onChange={(e) => setCustomInstruction(e.target.value)}
                    />

                    {/* Quick presets */}
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {QUICK_PROMPT_PRESETS.map((p, idx) => (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => setCustomInstruction(p.text)}
                          className="px-2 py-1 text-[10px] bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-md transition font-medium"
                        >
                          {p.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Nút hành động Submit */}
                  <div className="pt-2">
                    <Button
                      variant="primary"
                      size="lg"
                      type="submit"
                      disabled={isGenerating}
                      className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 shadow-md transition"
                    >
                      {isGenerating ? (
                        <span className="flex items-center justify-center gap-2">
                          <span className="animate-spin text-base">✨</span>
                          AI đang sáng tạo nội dung...
                        </span>
                      ) : (
                        <span className="flex items-center justify-center gap-2">
                          <span>✨</span>
                          Sáng tạo ngay bằng AI
                        </span>
                      )}
                    </Button>
                  </div>
                </form>
              </Card>
            </div>

            {/* CỘT PHẢI: KẾT QUẢ SINH NỘI DUNG & XEM TRƯỚC (7 Cột) */}
            <div className="lg:col-span-7 space-y-6">
              {isGenerating ? (
                <div className="bg-white rounded-xl border border-slate-200 p-12 text-center shadow-xs">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-emerald-100 text-emerald-600 flex items-center justify-center text-3xl animate-bounce">
                    ✨
                  </div>
                  <h3 className="text-base font-bold text-slate-800">
                    Mộc AI Assistant đang nghiên cứu dữ liệu sản phẩm...
                  </h3>
                  <p className="text-xs text-slate-500 mt-2 max-w-md mx-auto">
                    Áp dụng mô hình tâm lý học thuyết phục AIDA/PAS, tối ưu hóa từ khóa dinh dưỡng và tạo phân cảnh storyboard hấp dẫn.
                  </p>
                </div>
              ) : !generationResult ? (
                <div className="bg-white rounded-xl border border-dashed border-slate-300 p-12 text-center">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center text-2xl">
                    📝
                  </div>
                  <h3 className="text-base font-bold text-slate-700">Chưa có nội dung nào được tạo</h3>
                  <p className="text-xs text-slate-500 mt-2 max-w-sm mx-auto">
                    Chọn sản phẩm mục tiêu và kênh mạng xã hội ở cột bên trái, sau đó nhấn "Sáng tạo ngay bằng AI" để nhận bài viết hoàn chỉnh.
                  </p>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Variant Tabs Header */}
                  <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center justify-between shadow-2xs">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-700">Phiên bản đề xuất:</span>
                      <div className="flex gap-1.5">
                        {generationResult.variants.map((v, idx) => (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => setActiveVariantIndex(idx)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                              activeVariantIndex === idx
                                ? 'bg-emerald-600 text-white shadow-xs'
                                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                            }`}
                          >
                            Lựa chọn #{idx + 1}
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="text-[11px] text-slate-400">
                      Model: {generationResult.model_name}
                    </div>
                  </div>

                  {/* Active Variant Card */}
                  {currentVariant && (
                    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                      {/* Variant Bar */}
                      <div className="bg-slate-50 px-6 py-3.5 border-b border-slate-200 flex items-center justify-between">
                        <div>
                          <Badge variant="success" size="sm">
                            {channel} • {contentType}
                          </Badge>
                          <span className="ml-2 text-xs font-bold text-slate-800">
                            {currentVariant.title}
                          </span>
                        </div>

                        <div className="flex items-center gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() =>
                              handleCopyText(
                                `${currentVariant.title ? currentVariant.title + '\n\n' : ''}${
                                  currentVariant.hook ? '🔥 ' + currentVariant.hook + '\n\n' : ''
                                }${currentVariant.body}\n\n👉 ${currentVariant.cta}\n\n${currentVariant.hashtags.join(
                                  ' '
                                )}`,
                                activeVariantIndex
                              )
                            }
                          >
                            {copiedIndex === activeVariantIndex ? '✓ Đã sao chép' : '📋 Sao chép'}
                          </Button>

                          <Button
                            variant="primary"
                            size="sm"
                            disabled={savingIndex === activeVariantIndex}
                            onClick={() => handleSaveToLibrary(currentVariant, activeVariantIndex)}
                            className="bg-emerald-600 hover:bg-emerald-700 text-white"
                          >
                            {savingIndex === activeVariantIndex ? 'Đang lưu...' : '💾 Lưu vào Kho'}
                          </Button>
                        </div>
                      </div>

                      {/* Content Preview Body */}
                      <div className="p-6 space-y-4">
                        {currentVariant.hook && (
                          <div className="p-3 bg-amber-50/50 rounded-lg border border-amber-100">
                            <span className="text-[10px] font-bold uppercase tracking-wider text-amber-800 block mb-1">
                              Câu mở đầu thu hút (Hook 3s)
                            </span>
                            <p className="text-xs font-bold text-amber-950">
                              🔥 {currentVariant.hook}
                            </p>
                          </div>
                        )}

                        <div>
                          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                            Nội dung chi tiết (Body Content)
                          </span>
                          <div className="text-xs text-slate-800 whitespace-pre-line leading-relaxed font-sans bg-slate-50/50 p-4 rounded-lg border border-slate-100">
                            {currentVariant.body}
                          </div>
                        </div>

                        {/* Storyboard Suggestion View */}
                        {currentVariant.storyboard_suggestion && (
                          <div className="mt-4 pt-4 border-t border-slate-100">
                            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-700 block mb-2">
                              🎬 Kịch bản phân cảnh Video ngắn (Storyboard)
                            </span>
                            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-700 whitespace-pre-line">
                              {currentVariant.storyboard_suggestion}
                            </div>
                          </div>
                        )}

                        {/* CTA and Hashtags */}
                        <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-xs">
                          <div>
                            <span className="font-bold text-emerald-700">Lời kêu gọi (CTA): </span>
                            <span className="text-slate-800 font-semibold">
                              {currentVariant.cta}
                            </span>
                          </div>

                          <div className="flex flex-wrap gap-1">
                            {currentVariant.hashtags.map((tag, tIdx) => (
                              <span
                                key={tIdx}
                                className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-[11px] font-medium"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </AdminShell>
  );
}
