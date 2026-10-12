'use client';

import React from 'react';
import {
  WorkflowDetailResponse,
  WorkflowListItem,
} from '@moc-healthy/contracts';
import { Badge, Button } from '@moc-healthy/ui';

interface WorkflowDetailDrawerProps {
  workflow: WorkflowDetailResponse | null;
  isOpen: boolean;
  onClose: () => void;
  onTestRun: (workflow: WorkflowListItem) => void;
  onToggleStatus: (workflowId: string, currentStatus: string) => Promise<void>;
  onEdit: (workflow: WorkflowListItem) => void;
}

const TRIGGER_LABELS: Record<string, { label: string; icon: string; color: string }> = {
  CUSTOMER_CREATED: { label: 'Khách hàng mới tạo', icon: '👤', color: 'bg-blue-50 text-blue-700' },
  CART_ABANDONED: { label: 'Giỏ hàng bỏ quên', icon: '🛒', color: 'bg-amber-50 text-amber-700' },
  ORDER_COMPLETED: { label: 'Đơn hàng hoàn tất', icon: '✅', color: 'bg-emerald-50 text-emerald-700' },
  CUSTOMER_INACTIVE: { label: 'Khách không mua hàng lâu', icon: '💤', color: 'bg-purple-50 text-purple-700' },
  INVENTORY_EXPIRY_RISK: { label: 'Tồn kho cận date', icon: '⏰', color: 'bg-rose-50 text-rose-700' },
  LOW_STOCK: { label: 'Tồn kho thấp', icon: '📦', color: 'bg-orange-50 text-orange-700' },
  CAMPAIGN_ENDING: { label: 'Chiến dịch sắp kết thúc', icon: '🏁', color: 'bg-indigo-50 text-indigo-700' },
};

const ACTION_LABELS: Record<string, { label: string; icon: string }> = {
  SEND_ZALO_MOCK: { label: 'Gửi tin Zalo OA / ZNS', icon: '💬' },
  SEND_EMAIL_MOCK: { label: 'Gửi Email Marketing', icon: '✉️' },
  ISSUE_PROMOTION: { label: 'Tặng mã Voucher Khuyến mãi', icon: '🎟️' },
  ADD_LOYALTY_POINTS: { label: 'Tích lũy Điểm thưởng Mộc Xu', icon: '⭐' },
  ADD_CUSTOMER_TAG: { label: 'Gắn thẻ Phân loại Khách hàng', icon: '🏷️' },
  CREATE_NOTIFICATION: { label: 'Tạo Thông báo Hệ thống', icon: '🔔' },
  CREATE_RECOMMENDATION: { label: 'Đề xuất Chiến lược AI', icon: '💡' },
  CREATE_CAMPAIGN_DRAFT: { label: 'Tạo Bản nháp Chiến dịch Marketing', icon: '📋' },
  WAIT_HOURS: { label: 'Tạm dừng chờ thời gian', icon: '⏳' },
};

export const WorkflowDetailDrawer: React.FC<WorkflowDetailDrawerProps> = ({
  workflow,
  isOpen,
  onClose,
  onTestRun,
  onToggleStatus,
  onEdit,
}) => {
  if (!isOpen || !workflow) return null;

  const triggerMeta = TRIGGER_LABELS[workflow.trigger_type] || {
    label: workflow.trigger_type,
    icon: '⚡',
    color: 'bg-gray-100 text-gray-700',
  };

  const isActive = workflow.status === 'ACTIVE';

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity" onClick={onClose} />
      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-2xl bg-white shadow-2xl flex flex-col">
          {/* Header */}
          <div className="p-6 border-b border-slate-100 flex items-start justify-between bg-slate-50/50">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${triggerMeta.color}`}>
                  <span>{triggerMeta.icon}</span>
                  <span>{triggerMeta.label}</span>
                </span>
                <span className="font-mono text-xs text-slate-500 bg-slate-200/60 px-2 py-0.5 rounded">
                  {workflow.code}
                </span>
                {workflow.is_system_template && (
                  <span className="text-xs bg-emerald-100 text-emerald-800 font-medium px-2 py-0.5 rounded">
                    Mẫu hệ thống
                  </span>
                )}
                <Badge variant={isActive ? 'success' : 'neutral'}>
                  {isActive ? 'ĐANG CHẠY' : workflow.status}
                </Badge>
              </div>
              <h2 className="text-xl font-bold text-slate-800">{workflow.name}</h2>
              {workflow.description && (
                <p className="text-sm text-slate-600 mt-1">{workflow.description}</p>
              )}
            </div>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-600 p-2 rounded-lg hover:bg-slate-100 transition-colors"
            >
              ✕
            </button>
          </div>

          {/* Body Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Quick Metrics */}
            <div className="grid grid-cols-4 gap-3 bg-slate-50 p-4 rounded-xl border border-slate-100 text-center">
              <div>
                <p className="text-xs text-slate-500">Tổng lượt chạy</p>
                <p className="text-lg font-bold text-slate-800">{workflow.total_runs}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Thành công</p>
                <p className="text-lg font-bold text-emerald-600">{workflow.successful_runs}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Thất bại</p>
                <p className="text-lg font-bold text-rose-500">{workflow.failed_runs}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Tỷ lệ thành công</p>
                <p className="text-lg font-bold text-blue-600">{workflow.success_rate}%</p>
              </div>
            </div>

            {/* Conditions Section */}
            <div>
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <span>🎯</span> Điều kiện kích hoạt ({workflow.conditions?.length || 0})
              </h3>
              {(!workflow.conditions || workflow.conditions.length === 0) ? (
                <div className="p-3 bg-slate-50 rounded-lg text-xs text-slate-500 italic border border-slate-100">
                  Không có điều kiện ràng buộc (luôn thực thi khi sự kiện xảy ra).
                </div>
              ) : (
                <div className="space-y-2">
                  {workflow.conditions.map((c, i) => (
                    <div key={i} className="flex items-center gap-2 p-2.5 bg-amber-50/50 border border-amber-200/60 rounded-lg text-xs text-slate-700">
                      <span className="font-semibold text-amber-700">IF</span>
                      <code className="bg-amber-100/70 px-1.5 py-0.5 rounded font-mono font-medium">{c.field}</code>
                      <span className="text-slate-500 font-mono font-bold">{c.operator}</span>
                      <code className="bg-white px-2 py-0.5 rounded border border-amber-200 font-mono font-bold text-slate-800">
                        {String(c.value)}
                      </code>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Actions Sequence Section */}
            <div>
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <span>⚡</span> Chuỗi hành động thực thi ({workflow.actions?.length || 0} bước)
              </h3>
              <div className="space-y-2.5">
                {workflow.actions?.map((act, i) => {
                  const meta = ACTION_LABELS[act.type] || { label: act.type, icon: '⚙️' };
                  return (
                    <div key={i} className="p-3.5 bg-white border border-slate-200 rounded-xl shadow-sm relative pl-10">
                      <div className="absolute left-3 top-3.5 w-5 h-5 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold flex items-center justify-center">
                        {i + 1}
                      </div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                          <span>{meta.icon}</span>
                          <span>{meta.label}</span>
                        </span>
                        <span className="text-[10px] font-mono text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                          {act.type}
                        </span>
                      </div>
                      {act.message && (
                        <p className="text-xs text-slate-600 bg-slate-50 p-2 rounded border border-slate-100 mt-1 italic">
                          "{act.message}"
                        </p>
                      )}
                      <div className="flex flex-wrap gap-2 mt-2">
                        {act.promotion_code && (
                          <span className="text-[11px] bg-rose-50 text-rose-700 font-mono px-2 py-0.5 rounded border border-rose-100">
                            🎟️ Voucher: {act.promotion_code}
                          </span>
                        )}
                        {act.points && (
                          <span className="text-[11px] bg-amber-50 text-amber-700 font-mono px-2 py-0.5 rounded border border-amber-100">
                            ⭐ Điểm: +{act.points} Mộc Xu
                          </span>
                        )}
                        {act.tag && (
                          <span className="text-[11px] bg-blue-50 text-blue-700 font-mono px-2 py-0.5 rounded border border-blue-100">
                            🏷️ Tag: {act.tag}
                          </span>
                        )}
                        {act.wait_hours && (
                          <span className="text-[11px] bg-purple-50 text-purple-700 font-mono px-2 py-0.5 rounded border border-purple-100">
                            ⏳ Chờ: {act.wait_hours} giờ
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Recent Execution Runs */}
            <div>
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <span>📜</span> Lượt chạy gần đây ({workflow.recent_runs?.length || 0})
              </h3>
              {(!workflow.recent_runs || workflow.recent_runs.length === 0) ? (
                <div className="p-4 bg-slate-50 rounded-xl text-center text-xs text-slate-500 border border-slate-100">
                  Chưa có lượt chạy nào được ghi nhận. Bấm "🚀 Chạy thử nghiệm" bên dưới để kiểm thử.
                </div>
              ) : (
                <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden bg-white">
                  {workflow.recent_runs.map((r) => (
                    <div key={r.id} className="p-3 flex items-center justify-between text-xs hover:bg-slate-50">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${r.status === 'SUCCESS' ? 'bg-emerald-500' : 'bg-rose-500'}`} />
                          <span className="font-semibold text-slate-700">{r.status}</span>
                          <span className="text-slate-400">·</span>
                          <span className="text-slate-500">{new Date(r.created_at).toLocaleString('vi-VN')}</span>
                        </div>
                        {r.trigger_source_id && (
                          <p className="text-[11px] text-slate-400 mt-0.5">Source: {r.trigger_source_id}</p>
                        )}
                      </div>
                      <div className="text-right">
                        <span className="text-slate-600 bg-slate-100 px-2 py-0.5 rounded text-[11px]">
                          {r.step_count} bước
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Footer Actions */}
          <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Button
                variant={isActive ? 'outline' : 'primary'}
                size="sm"
                onClick={() => onToggleStatus(workflow.id, isActive ? 'PAUSED' : 'ACTIVE')}
              >
                {isActive ? '⏸️ Tạm dừng' : '▶️ Bật kích hoạt'}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onEdit(workflow)}
              >
                ✏️ Chỉnh sửa
              </Button>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="primary"
                size="sm"
                onClick={() => onTestRun(workflow)}
              >
                🚀 Chạy thử (Dry-run)
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
