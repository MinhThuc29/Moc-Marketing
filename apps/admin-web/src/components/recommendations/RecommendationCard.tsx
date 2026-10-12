'use client';

import React from 'react';
import { Badge, Button } from '@moc-healthy/ui';
import { AIRecommendationItem } from '@moc-healthy/contracts';

interface RecommendationCardProps {
  recommendation: AIRecommendationItem;
  onConvertToCampaign: (rec: AIRecommendationItem) => void;
  onConvertToAutomation: (rec: AIRecommendationItem) => void;
  onDismiss: (rec: AIRecommendationItem) => void;
  isConverting?: boolean;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  recommendation,
  onConvertToCampaign,
  onConvertToAutomation,
  onDismiss,
  isConverting = false,
}) => {
  const getTypeBadge = (type: string) => {
    switch (type) {
      case 'INVENTORY_CLEARANCE':
        return <Badge variant="warning">📦 Xả kho cận date</Badge>;
      case 'CAMPAIGN_OPPORTUNITY':
        return <Badge variant="success">🚀 Cơ hội chiến dịch</Badge>;
      case 'CUSTOMER_RETENTION':
        return <Badge variant="info">👥 Giữ chân khách hàng</Badge>;
      case 'CHANNEL_OPTIMIZATION':
        return <Badge variant="neutral">⚡ Tối ưu biên lợi nhuận sàn</Badge>;
      default:
        return <Badge variant="neutral">{type}</Badge>;
    }
  };

  const getConfidenceBadge = (level: string, score: number) => {
    const percent = Math.round(score * 100);
    if (level === 'HIGH' || score >= 0.8) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse"></span>
          Độ tin cậy cao {percent}%
        </span>
      );
    }
    if (level === 'MEDIUM' || score >= 0.6) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-300">
          Độ tin cậy vừa {percent}%
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs bg-slate-100 text-slate-700">
        Khảo sát {percent}%
      </span>
    );
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PENDING':
        return <Badge variant="warning">⏳ Chờ duyệt</Badge>;
      case 'APPLIED':
        return <Badge variant="success">✅ Đã áp dụng</Badge>;
      case 'DISMISSED':
        return <Badge variant="neutral">🚫 Đã bỏ qua</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  return (
    <div className={`bg-white rounded-xl border p-5 transition-all shadow-sm hover:shadow-md ${
      recommendation.status === 'APPLIED' ? 'border-emerald-200 bg-emerald-50/20' : 'border-slate-200'
    }`}>
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2 flex-wrap">
          {getTypeBadge(recommendation.recommendation_type)}
          {getConfidenceBadge(recommendation.confidence_level, recommendation.confidence_score)}
          {getStatusBadge(recommendation.status)}
        </div>
        <span className="text-[11px] text-slate-400">
          {new Date(recommendation.created_at).toLocaleDateString('vi-VN', {
            day: '2-digit',
            month: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
          })}
        </span>
      </div>

      {/* Title */}
      <div className="mt-3">
        <h3 className="text-base font-bold text-slate-900 leading-snug">
          {recommendation.title}
        </h3>
        <p className="mt-2 text-xs text-slate-600 leading-relaxed">
          <strong className="text-slate-800 font-semibold">Vấn đề phân tích: </strong>
          {recommendation.problem_statement}
        </p>
      </div>

      {/* Evidence Box - Bằng chứng số học thực tế từ DB */}
      {recommendation.evidence && recommendation.evidence.length > 0 && (
        <div className="mt-4 p-3 bg-slate-50 rounded-lg border border-slate-200/80">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
              <span>📊</span> Bằng chứng dữ liệu xác thực (Single Source of Truth)
            </span>
            <span className="text-[10px] text-emerald-700 font-medium bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              Verified DB
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
            {recommendation.evidence.map((ev, idx) => (
              <div key={idx} className="bg-white p-2.5 rounded border border-slate-100 shadow-2xs">
                <p className="text-[10px] text-slate-400 font-medium uppercase truncate">{ev.metric}</p>
                <p className="text-xs font-bold text-slate-800 mt-0.5">{String(ev.value)}</p>
                <p className="text-[10px] text-slate-500 mt-1 truncate" title={ev.comparison}>
                  {ev.comparison}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommended Action */}
      <div className="mt-4 p-3.5 bg-emerald-50/60 rounded-lg border border-emerald-200/70">
        <div className="flex items-start gap-2">
          <span className="text-base leading-none mt-0.5">💡</span>
          <div>
            <p className="text-xs font-bold text-emerald-950">Hành động khuyến nghị bởi AI:</p>
            <p className="text-xs text-emerald-900 mt-1 leading-relaxed">
              {recommendation.recommended_action}
            </p>
          </div>
        </div>
      </div>

      {/* Channels & Expected Impact */}
      <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
        {recommendation.target_channels && recommendation.target_channels.length > 0 && (
          <div className="bg-slate-50/80 p-2.5 rounded-lg border border-slate-100">
            <span className="text-[11px] font-semibold text-slate-700 block mb-1.5">Kênh triển khai gợi ý:</span>
            <div className="flex flex-wrap gap-1.5">
              {recommendation.target_channels.map((ch, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 text-[11px] font-medium bg-white text-slate-700 rounded border border-slate-200"
                >
                  {ch}
                </span>
              ))}
            </div>
          </div>
        )}

        {recommendation.suggested_promotion && (
          <div className="bg-slate-50/80 p-2.5 rounded-lg border border-slate-100">
            <span className="text-[11px] font-semibold text-slate-700 block mb-1">Đề xuất ưu đãi:</span>
            <p className="text-xs text-slate-800 font-medium">
              Mã: <code className="bg-emerald-100 px-1.5 py-0.5 rounded text-emerald-800 font-bold text-xs">{recommendation.suggested_promotion.code || 'PROMO'}</code>
              {recommendation.suggested_promotion.discount_value && (
                <span className="ml-1 text-slate-600">
                  (Giảm {recommendation.suggested_promotion.discount_value}%)
                </span>
              )}
            </p>
          </div>
        )}
      </div>

      {/* Action Footer */}
      <div className="mt-5 pt-3.5 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          {recommendation.risks && recommendation.risks.length > 0 && (
            <span className="text-[11px] text-amber-700 bg-amber-50 px-2 py-1 rounded border border-amber-200/60" title={recommendation.risks.join('; ')}>
              ⚠️ Lưu ý: {recommendation.risks[0]}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {recommendation.status === 'PENDING' ? (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onDismiss(recommendation)}
                disabled={isConverting}
                className="text-xs text-slate-600 hover:text-slate-800"
              >
                Bỏ qua
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onConvertToAutomation(recommendation)}
                disabled={isConverting}
                className="text-xs border-emerald-300 text-emerald-700 hover:bg-emerald-50"
              >
                ⚡ 1-Click: Tạo Workflow
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => onConvertToCampaign(recommendation)}
                disabled={isConverting}
                className="text-xs bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                🚀 1-Click: Tạo Chiến dịch
              </Button>
            </>
          ) : (
            <div className="text-xs text-emerald-700 font-medium flex items-center gap-1.5">
              <span>Đã chuyển đổi thành công</span>
              {recommendation.converted_campaign_id && (
                <a
                  href="/marketing"
                  className="underline font-semibold hover:text-emerald-900"
                >
                  (Xem chiến dịch)
                </a>
              )}
              {recommendation.converted_workflow_id && (
                <a
                  href="/automation"
                  className="underline font-semibold hover:text-emerald-900"
                >
                  (Xem workflow)
                </a>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
