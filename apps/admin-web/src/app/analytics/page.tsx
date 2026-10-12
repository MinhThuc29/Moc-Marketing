'use client';

import React, { useState, useEffect } from 'react';
import { AdminShell } from '../../components/shell/AdminShell';
import { PageHeader } from '../../components/shell/PageHeader';
import { Badge, Button, Card, Skeleton } from '@moc-healthy/ui';
import {
  AnalyticsDashboardResponse,
  ChannelAnalyticsItem,
  CampaignAttributionComparison,
  FunnelStepItem,
  AIAnalyticsInsightItem,
} from '@moc-healthy/contracts';
import { analyticsApi } from '../../lib/api';

const formatVnd = (amount?: number | null) => {
  if (amount === undefined || amount === null) return '0đ';
  return `${Math.round(amount).toLocaleString('vi-VN')}đ`;
};

const formatPercent = (val?: number | null) => {
  if (val === undefined || val === null) return '0%';
  return `${val.toFixed(1)}%`;
};

type ActiveTab = 'channels' | 'attribution' | 'funnel' | 'insights';

export default function AnalyticsPage() {
  const [period, setPeriod] = useState<string>('30d');
  const [activeTab, setActiveTab] = useState<ActiveTab>('channels');
  const [data, setData] = useState<AnalyticsDashboardResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    loadData(period);
  }, [period]);

  const loadData = async (selectedPeriod: string) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await analyticsApi.getOverview({ period: selectedPeriod });
      setData(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'Không thể tải báo cáo phân tích tiếp thị');
    } finally {
      setIsLoading(false);
    }
  };

  const kpis = data?.kpis;

  return (
    <AdminShell requiredPermission="analytics.read">
      <PageHeader
        title="Marketing Analytics & Attribution Engine"
        subtitle="Phân tích doanh thu đa kênh, đối soát Gross vs Net, phân bổ đa điểm chạm (Multi-touch Attribution) & AI Insights"
        breadcrumbs={[{ label: 'Báo cáo & Phân bổ Tiếp thị' }]}
        actions={
          <div className="flex items-center gap-3">
            <div className="flex bg-slate-100 p-0.5 rounded-lg border border-slate-200">
              <button
                type="button"
                onClick={() => setPeriod('7d')}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                  period === '7d'
                    ? 'bg-white text-emerald-700 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                7 ngày qua
              </button>
              <button
                type="button"
                onClick={() => setPeriod('30d')}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                  period === '30d'
                    ? 'bg-white text-emerald-700 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                30 ngày qua
              </button>
              <button
                type="button"
                onClick={() => setPeriod('90d')}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                  period === '90d'
                    ? 'bg-white text-emerald-700 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Quý này (90d)
              </button>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => loadData(period)}
              disabled={isLoading}
            >
              🔄 {isLoading ? 'Đang tải...' : 'Làm mới'}
            </Button>
          </div>
        }
      />

      {errorMsg && (
        <div className="mb-6 p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span>⚠️</span>
            <span>{errorMsg}</span>
          </div>
          <button
            onClick={() => setErrorMsg(null)}
            className="text-xs font-semibold text-rose-600 hover:underline"
          >
            Đóng
          </button>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 1. TOP 6 EXECUTIVE KPI CARDS                                              */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-8">
        {/* Card 1: Gross & Net Revenue */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/90 shadow-xs space-y-2">
          <div className="text-[11px] font-semibold uppercase text-slate-500 tracking-wider">
            Doanh Thu Gộp (Gross)
          </div>
          <div className="text-xl font-bold text-slate-900">
            {isLoading ? <Skeleton className="h-7 w-28" /> : formatVnd(kpis?.gross_revenue)}
          </div>
          <div className="text-[11px] text-emerald-600 font-medium flex items-center gap-1">
            <span>Thực nhận Net:</span>
            <strong>{formatVnd(kpis?.net_revenue)}</strong>
          </div>
        </div>

        {/* Card 2: Attributed Revenue */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/90 shadow-xs space-y-2">
          <div className="text-[11px] font-semibold uppercase text-slate-500 tracking-wider">
            Doanh Thu Tiếp Thị
          </div>
          <div className="text-xl font-bold text-emerald-600">
            {isLoading ? <Skeleton className="h-7 w-28" /> : formatVnd(kpis?.attributed_revenue)}
          </div>
          <div className="text-[11px] text-slate-500">
            Tỷ lệ gắn tiếp thị:{' '}
            <strong className="text-emerald-700">{formatPercent(kpis?.attribution_rate)}</strong>
          </div>
        </div>

        {/* Card 3: Marketing Spend & ROAS */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/90 shadow-xs space-y-2">
          <div className="text-[11px] font-semibold uppercase text-slate-500 tracking-wider">
            Chi Phí Quảng Cáo
          </div>
          <div className="text-xl font-bold text-rose-600">
            {isLoading ? <Skeleton className="h-7 w-28" /> : formatVnd(kpis?.marketing_spend)}
          </div>
          <div className="text-[11px] text-slate-500 flex items-center justify-between">
            <span>Blended ROAS:</span>
            <Badge variant="success">{kpis?.roas ? `${kpis.roas}x` : '---'}</Badge>
          </div>
        </div>

        {/* Card 4: MER & Total Orders */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/90 shadow-xs space-y-2">
          <div className="text-[11px] font-semibold uppercase text-slate-500 tracking-wider">
            MER (Hiệu quả chi phí)
          </div>
          <div className="text-xl font-bold text-indigo-600">
            {isLoading ? <Skeleton className="h-7 w-24" /> : `${kpis?.mer || 0}x`}
          </div>
          <div className="text-[11px] text-slate-500">
            Tổng đơn hàng: <strong>{kpis?.total_orders || 0} đơn</strong>
          </div>
        </div>

        {/* Card 5: CAC & New Customers */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/90 shadow-xs space-y-2">
          <div className="text-[11px] font-semibold uppercase text-slate-500 tracking-wider">
            Chi Phí Khách Mới (CAC)
          </div>
          <div className="text-xl font-bold text-amber-600">
            {isLoading ? <Skeleton className="h-7 w-28" /> : formatVnd(kpis?.cac)}
          </div>
          <div className="text-[11px] text-slate-500">
            Khách mới: <strong>+{kpis?.new_customers || 0} khách</strong>
          </div>
        </div>

        {/* Card 6: LTV & LTV/CAC */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/90 shadow-xs space-y-2">
          <div className="text-[11px] font-semibold uppercase text-slate-500 tracking-wider">
            Giá Trị Vòng Đời (LTV)
          </div>
          <div className="text-xl font-bold text-blue-600">
            {isLoading ? <Skeleton className="h-7 w-28" /> : formatVnd(kpis?.ltv)}
          </div>
          <div className="text-[11px] text-slate-500 flex items-center justify-between">
            <span>LTV / CAC:</span>
            <span className="font-bold text-emerald-600">{kpis?.ltv_to_cac_ratio || 0}x</span>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 2. TAB CONTROLS                                                           */}
      {/* ========================================================================= */}
      <div className="flex items-center gap-2 border-b border-slate-200 mb-6 overflow-x-auto">
        <button
          onClick={() => setActiveTab('channels')}
          className={`pb-3 px-4 text-xs font-semibold border-b-2 transition-colors whitespace-nowrap flex items-center gap-1.5 ${
            activeTab === 'channels'
              ? 'border-emerald-600 text-emerald-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <span>📊</span> Báo Cáo Đa Kênh (Omnichannel P&L)
        </button>
        <button
          onClick={() => setActiveTab('attribution')}
          className={`pb-3 px-4 text-xs font-semibold border-b-2 transition-colors whitespace-nowrap flex items-center gap-1.5 ${
            activeTab === 'attribution'
              ? 'border-emerald-600 text-emerald-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <span>🎯</span> Phân Bổ Tiếp Thị (Attribution Engine)
        </button>
        <button
          onClick={() => setActiveTab('funnel')}
          className={`pb-3 px-4 text-xs font-semibold border-b-2 transition-colors whitespace-nowrap flex items-center gap-1.5 ${
            activeTab === 'funnel'
              ? 'border-emerald-600 text-emerald-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <span>🌪️</span> Phễu Chuyển Đổi (Funnel)
        </button>
        <button
          onClick={() => setActiveTab('insights')}
          className={`pb-3 px-4 text-xs font-semibold border-b-2 transition-colors whitespace-nowrap flex items-center gap-1.5 ${
            activeTab === 'insights'
              ? 'border-emerald-600 text-emerald-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <span>💡</span> AI Insights & Tối Ưu ({data?.ai_insights.length || 0})
        </button>
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: OMNICHANNEL P&L BREAKDOWN                                          */}
      {/* ========================================================================= */}
      {activeTab === 'channels' && (
        <div className="space-y-6">
          <Card title="Doanh Thu Đa Kênh: Phân Tách Doanh Thu Gộp (Gross) vs Thực Nhận (Net)">
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left text-slate-600">
                <thead className="bg-slate-50 text-[11px] font-bold text-slate-700 uppercase border-b border-slate-200">
                  <tr>
                    <th className="py-3 px-4">Kênh Bán Hàng</th>
                    <th className="py-3 px-3 text-center">Số Đơn</th>
                    <th className="py-3 px-4 text-right">Doanh Thu Gộp</th>
                    <th className="py-3 px-3 text-right">Phí Sàn / Chiết Khấu</th>
                    <th className="py-3 px-4 text-right">Thực Nhận (Net)</th>
                    <th className="py-3 px-3 text-center">Biên Lợi Nhuận</th>
                    <th className="py-3 px-3 text-right">AOV</th>
                    <th className="py-3 px-3 text-right">Tỷ Trọng</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-sans">
                  {data?.channel_breakdown.map((ch) => (
                    <tr key={ch.channel} className="hover:bg-slate-50/60 transition-colors">
                      <td className="py-3 px-4 font-semibold text-slate-900 flex items-center gap-2">
                        <span>
                          {ch.channel === 'WEBSITE'
                            ? '🌐'
                            : ch.channel === 'GRAB'
                            ? '🛵'
                            : ch.channel === 'SHOPEEFOOD'
                            ? '🍲'
                            : ch.channel === 'ZALO'
                            ? '💬'
                            : ch.channel === 'FACEBOOK'
                            ? '📘'
                            : '🏬'}
                        </span>
                        {ch.channel_name}
                      </td>
                      <td className="py-3 px-3 text-center font-medium">{ch.orders_count}</td>
                      <td className="py-3 px-4 text-right font-medium text-slate-800">
                        {formatVnd(ch.gross_sales)}
                      </td>
                      <td className="py-3 px-3 text-right text-rose-600 font-medium">
                        {ch.platform_fees > 0 ? `-${formatVnd(ch.platform_fees)}` : '---'}
                      </td>
                      <td className="py-3 px-4 text-right font-bold text-emerald-700">
                        {formatVnd(ch.net_revenue)}
                      </td>
                      <td className="py-3 px-3 text-center">
                        <span
                          className={`inline-block px-2 py-0.5 rounded-full text-[11px] font-semibold ${
                            ch.net_margin_percentage >= 90
                              ? 'bg-emerald-100 text-emerald-800'
                              : ch.net_margin_percentage >= 75
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-amber-100 text-amber-800'
                          }`}
                        >
                          {formatPercent(ch.net_margin_percentage)}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-right text-slate-700 font-medium">
                        {formatVnd(ch.aov)}
                      </td>
                      <td className="py-3 px-3 text-right font-bold text-slate-600">
                        {formatPercent(ch.share_of_sales)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-4 p-3 bg-slate-50 rounded-lg border border-slate-200 text-[11px] text-slate-500 leading-relaxed flex items-center gap-2">
              <span className="text-base">📌</span>
              <span>
                <strong>Ghi chú bóc tách tài chính:</strong> Kênh Owned Web (Website Mộc Healthy)
                và Zalo OA đạt biên thực nhận 100% dòng tiền (không chi trả hoa hồng 20-25% cho sàn).
                Các đơn sàn GrabFood/ShopeeFood được tính toán phí tự động qua báo cáo đối soát.
              </span>
            </div>
          </Card>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: MULTI-TOUCH ATTRIBUTION COMPARISON                                 */}
      {/* ========================================================================= */}
      {activeTab === 'attribution' && (
        <div className="space-y-6">
          {/* Hướng dẫn Attribution */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-emerald-50/60 border border-emerald-200/60 rounded-xl space-y-1">
              <div className="text-xs font-bold text-emerald-800 uppercase flex items-center gap-1.5">
                <span>1️⃣</span> First-Touch Model
              </div>
              <p className="text-[11px] text-emerald-950/80 leading-relaxed">
                Ghi nhận 100% công sức cho điểm chạm tiếp thị đầu tiên đưa khách hàng biết đến Mộc
                Healthy (Tối ưu đo lường Awareness & Thu hút khách mới).
              </p>
            </div>
            <div className="p-4 bg-blue-50/60 border border-blue-200/60 rounded-xl space-y-1">
              <div className="text-xs font-bold text-blue-800 uppercase flex items-center gap-1.5">
                <span>🎯</span> Last-Touch Model
              </div>
              <p className="text-[11px] text-blue-950/80 leading-relaxed">
                Ghi nhận 100% công sức cho kênh cuối cùng khách nhấp vào trước khi đặt hàng (Đo lường
                năng lực chốt đơn & Conversion).
              </p>
            </div>
            <div className="p-4 bg-indigo-50/60 border border-indigo-200/60 rounded-xl space-y-1">
              <div className="text-xs font-bold text-indigo-800 uppercase flex items-center gap-1.5">
                <span>⚖️</span> Linear Model
              </div>
              <p className="text-[11px] text-indigo-950/80 leading-relaxed">
                Chia đều credit doanh thu cho tất cả các điểm chạm trong hành trình khách hàng trước
                khi hoàn tất đơn hàng.
              </p>
            </div>
          </div>

          <Card title="So Sánh Hiệu Quả Các Chiến Dịch Tiếp Thị Theo Mô Hình Phân Bổ">
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left text-slate-600">
                <thead className="bg-slate-50 text-[11px] font-bold text-slate-700 uppercase border-b border-slate-200">
                  <tr>
                    <th className="py-3 px-4">Chiến Dịch Marketing</th>
                    <th className="py-3 px-3">Kênh</th>
                    <th className="py-3 px-3 text-right">Chi Phí</th>
                    <th className="py-3 px-4 text-right">Doanh Thu (First)</th>
                    <th className="py-3 px-3 text-center">ROAS (First)</th>
                    <th className="py-3 px-4 text-right">Doanh Thu (Last)</th>
                    <th className="py-3 px-3 text-center">ROAS (Last)</th>
                    <th className="py-3 px-3 text-center">Độ Tin Cậy</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-sans">
                  {data?.campaign_attributions.map((ca) => (
                    <tr key={ca.campaign_id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-900">{ca.campaign_name}</div>
                        <div className="text-[10px] text-slate-400 font-mono">{ca.campaign_code}</div>
                      </td>
                      <td className="py-3 px-3">
                        <Badge variant="neutral">{ca.channel}</Badge>
                      </td>
                      <td className="py-3 px-3 text-right font-medium text-rose-600">
                        {formatVnd(ca.spend)}
                      </td>
                      <td className="py-3 px-4 text-right font-semibold text-slate-800">
                        {formatVnd(ca.first_touch_revenue)}
                      </td>
                      <td className="py-3 px-3 text-center">
                        <span className="font-bold text-emerald-700">{ca.first_touch_roas}x</span>
                      </td>
                      <td className="py-3 px-4 text-right font-bold text-emerald-700">
                        {formatVnd(ca.last_touch_revenue)}
                      </td>
                      <td className="py-3 px-3 text-center">
                        <span className="font-bold text-emerald-800">{ca.last_touch_roas}x</span>
                      </td>
                      <td className="py-3 px-3 text-center">
                        <Badge
                          variant={
                            ca.confidence === 'DETERMINISTIC'
                              ? 'success'
                              : ca.confidence === 'INFERRED'
                              ? 'info'
                              : 'warning'
                          }
                        >
                          {ca.confidence === 'DETERMINISTIC'
                            ? '🎯 Trực tiếp (Click)'
                            : ca.confidence === 'INFERRED'
                            ? '🔍 Suy luận (Voucher)'
                            : 'Tập hợp'}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: CONVERSION FUNNEL                                                  */}
      {/* ========================================================================= */}
      {activeTab === 'funnel' && (
        <div className="space-y-6">
          <Card title="Phễu Hành Vi & Tỷ Lệ Chuyển Đổi Mua Hàng (5-Step Conversion Funnel)">
            <div className="space-y-6 py-2">
              {data?.funnel.map((step, idx) => {
                const widthPercent = Math.max(step.conversion_from_top, 8);
                return (
                  <div key={step.step_key} className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <div className="font-semibold text-slate-800 flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-slate-100 flex items-center justify-center text-[11px] font-bold text-slate-700">
                          {idx + 1}
                        </span>
                        <span>{step.step_name}</span>
                      </div>
                      <div className="flex items-center gap-4 text-xs font-sans">
                        <span className="font-bold text-slate-900">
                          {step.count.toLocaleString('vi-VN')} lượt
                        </span>
                        <span className="text-emerald-700 font-semibold w-16 text-right">
                          {formatPercent(step.conversion_from_top)}
                        </span>
                        {idx > 0 && (
                          <span className="text-rose-600 text-[11px] w-24 text-right">
                            Drop: -{formatPercent(step.drop_off_rate)}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Funnel Bar */}
                    <div className="w-full bg-slate-100 h-5 rounded-lg overflow-hidden relative shadow-inner">
                      <div
                        className={`h-full rounded-lg transition-all duration-500 ${
                          idx === 0
                            ? 'bg-slate-400'
                            : idx === 1
                            ? 'bg-blue-500'
                            : idx === 2
                            ? 'bg-amber-500'
                            : idx === 3
                            ? 'bg-indigo-500'
                            : 'bg-emerald-600'
                        }`}
                        style={{ width: `${widthPercent}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="mt-8 pt-6 border-t border-slate-100 grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
              <div className="p-3 bg-slate-50 rounded-xl">
                <div className="text-[11px] text-slate-500 mb-1">Tỷ Lệ Chuyển Đổi Chung</div>
                <div className="text-lg font-bold text-emerald-700">
                  {data?.funnel[4] ? formatPercent(data.funnel[4].conversion_from_top) : '---'}
                </div>
              </div>
              <div className="p-3 bg-slate-50 rounded-xl">
                <div className="text-[11px] text-slate-500 mb-1">Tỷ Lệ Xem Món Sang Giỏ</div>
                <div className="text-lg font-bold text-blue-700">
                  {data?.funnel[2] ? `${Math.round(100 - data.funnel[2].drop_off_rate)}%` : '---'}
                </div>
              </div>
              <div className="p-3 bg-slate-50 rounded-xl">
                <div className="text-[11px] text-slate-500 mb-1">Tỷ Lệ Checkout Hoàn Tất</div>
                <div className="text-lg font-bold text-indigo-700">
                  {data?.funnel[4] ? `${Math.round(100 - data.funnel[4].drop_off_rate)}%` : '---'}
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 4: AI ANALYTICS INSIGHTS                                              */}
      {/* ========================================================================= */}
      {activeTab === 'insights' && (
        <div className="space-y-4">
          <div className="text-xs text-slate-500 mb-2">
            AI Engine tự động đối soát số liệu đa kênh và đưa ra các khuyến nghị tối ưu ngân sách
            kinh doanh thực phẩm Healthy:
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data?.ai_insights.map((insight, idx) => (
              <div
                key={idx}
                className={`p-5 rounded-xl border shadow-xs space-y-3 transition-all ${
                  insight.type === 'SUCCESS'
                    ? 'bg-emerald-50/70 border-emerald-200'
                    : insight.type === 'WARNING'
                    ? 'bg-amber-50/70 border-amber-200'
                    : 'bg-blue-50/70 border-blue-200'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">
                      {insight.type === 'SUCCESS' ? '🚀' : insight.type === 'WARNING' ? '⚠️' : '💡'}
                    </span>
                    <h4 className="text-xs font-bold text-slate-900 leading-snug">
                      {insight.title}
                    </h4>
                  </div>
                  {insight.metric_highlight && (
                    <Badge
                      variant={
                        insight.type === 'SUCCESS'
                          ? 'success'
                          : insight.type === 'WARNING'
                          ? 'warning'
                          : 'info'
                      }
                    >
                      {insight.metric_highlight}
                    </Badge>
                  )}
                </div>

                <p className="text-xs text-slate-700 leading-relaxed">{insight.description}</p>

                {insight.suggested_action && (
                  <div className="pt-2 border-t border-slate-200/60 text-xs font-medium text-slate-900 flex items-center gap-1.5">
                    <span className="text-emerald-700 font-bold">👉 Hành động đề xuất:</span>
                    <span>{insight.suggested_action}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </AdminShell>
  );
}
