'use client';

import React, { useState, useEffect } from 'react';
import {
  WorkflowListItem,
  WorkflowCreateInput,
  WorkflowUpdateInput,
  ConditionItem,
  ActionItem,
} from '@moc-healthy/contracts';
import { automationApi } from '../../lib/api';
import { Button } from '@moc-healthy/ui';

interface WorkflowFormModalProps {
  isOpen: boolean;
  workflow: WorkflowListItem | null;
  onClose: () => void;
  onSuccess: () => void;
}

const TRIGGER_OPTIONS = [
  { value: 'CUSTOMER_CREATED', label: '👤 Khách hàng mới tạo (Customer Created)' },
  { value: 'CART_ABANDONED', label: '🛒 Giỏ hàng bỏ quên (Abandoned Cart)' },
  { value: 'ORDER_COMPLETED', label: '✅ Đơn hàng hoàn tất (Order Completed)' },
  { value: 'CUSTOMER_INACTIVE', label: '💤 Khách ngừng mua hàng lâu (Customer Inactive)' },
  { value: 'INVENTORY_EXPIRY_RISK', label: '⏰ Tồn kho cận date (Expiry Risk)' },
  { value: 'LOW_STOCK', label: '📦 Tồn kho thấp (Low Stock)' },
];

const ACTION_TYPE_OPTIONS = [
  { value: 'SEND_ZALO_MOCK', label: '💬 Gửi tin nhắn Zalo OA / ZNS' },
  { value: 'SEND_EMAIL_MOCK', label: '✉️ Gửi Email Marketing' },
  { value: 'ISSUE_PROMOTION', label: '🎟️ Tặng mã Voucher Khuyến mãi' },
  { value: 'ADD_LOYALTY_POINTS', label: '⭐ Tích lũy Điểm thưởng Mộc Xu' },
  { value: 'ADD_CUSTOMER_TAG', label: '🏷️ Gắn thẻ Phân loại Khách hàng' },
  { value: 'CREATE_NOTIFICATION', label: '🔔 Tạo Thông báo Hệ thống' },
  { value: 'CREATE_RECOMMENDATION', label: '💡 Đề xuất Chiến lược AI' },
  { value: 'WAIT_HOURS', label: '⏳ Tạm dừng chờ thời gian (Giờ)' },
];

export const WorkflowFormModal: React.FC<WorkflowFormModalProps> = ({
  isOpen,
  workflow,
  onClose,
  onSuccess,
}) => {
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [description, setDescription] = useState('');
  const [triggerType, setTriggerType] = useState('CUSTOMER_CREATED');
  const [status, setStatus] = useState('ACTIVE');
  const [conditions, setConditions] = useState<ConditionItem[]>([]);
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (workflow) {
      setName(workflow.name);
      setCode(workflow.code);
      setDescription(workflow.description || '');
      setTriggerType(workflow.trigger_type);
      setStatus(workflow.status);
      setConditions(workflow.conditions || []);
      setActions(workflow.actions || []);
    } else {
      setName('');
      setCode(`WF-CUSTOM-${Math.floor(100 + Math.random() * 900)}`);
      setDescription('');
      setTriggerType('CUSTOMER_CREATED');
      setStatus('ACTIVE');
      setConditions([{ field: 'consent_marketing', operator: 'eq', value: true }]);
      setActions([{ type: 'SEND_ZALO_MOCK', message: 'Chào mừng {customer_name} đến với Mộc Healthy!' }]);
    }
    setError(null);
  }, [workflow, isOpen]);

  if (!isOpen) return null;

  const handleAddCondition = () => {
    setConditions([...conditions, { field: 'segment', operator: 'eq', value: 'VIP' }]);
  };

  const handleRemoveCondition = (index: number) => {
    setConditions(conditions.filter((_, i) => i !== index));
  };

  const handleUpdateCondition = (index: number, key: keyof ConditionItem, val: any) => {
    const updated = [...conditions];
    updated[index] = { ...updated[index], [key]: val };
    setConditions(updated);
  };

  const handleAddAction = () => {
    setActions([...actions, { type: 'SEND_ZALO_MOCK', message: 'Thông điệp chăm sóc sức khỏe' }]);
  };

  const handleRemoveAction = (index: number) => {
    setActions(actions.filter((_, i) => i !== index));
  };

  const handleUpdateAction = (index: number, key: keyof ActionItem, val: any) => {
    const updated = [...actions];
    updated[index] = { ...updated[index], [key]: val };
    setActions(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Vui lòng nhập tên kịch bản tự động hóa');
      return;
    }
    if (!code.trim()) {
      setError('Vui lòng nhập mã kịch bản');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      if (workflow) {
        const updateData: WorkflowUpdateInput = {
          name: name.trim(),
          description: description.trim() || null,
          trigger_type: triggerType,
          conditions,
          actions,
          status,
        };
        await automationApi.updateWorkflow(workflow.id, updateData);
      } else {
        const createData: WorkflowCreateInput = {
          name: name.trim(),
          code: code.trim().toUpperCase(),
          description: description.trim() || null,
          trigger_type: triggerType,
          conditions,
          actions,
          status,
          is_system_template: false,
        };
        await automationApi.createWorkflow(createData);
      }

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Lỗi khi lưu kịch bản tự động hóa.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Modal Header */}
        <div className="p-6 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-800">
            {workflow ? 'Chỉnh Sửa Kịch Bản Tự Động Hóa' : 'Tạo Kịch Bản Tự Động Hóa Mới'}
          </h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-2 rounded-lg hover:bg-slate-100"
          >
            ✕
          </button>
        </div>

        {/* Modal Form */}
        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto space-y-5 flex-1">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg">
              {error}
            </div>
          )}

          {/* Basic Info */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Tên kịch bản <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="vd: Chào đón thành viên mới"
                className="w-full text-xs p-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Mã kịch bản <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                disabled={!!workflow}
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="vd: WF-WELCOME-02"
                className="w-full text-xs font-mono p-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500 uppercase disabled:bg-slate-100"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Mô tả mục tiêu kịch bản
            </label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Mô tả khi nào kịch bản này kích hoạt và mang lại giá trị gì cho khách hàng..."
              className="w-full text-xs p-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>

          {/* Trigger & Status */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Sự kiện Kích hoạt (Trigger) <span className="text-rose-500">*</span>
              </label>
              <select
                value={triggerType}
                onChange={(e) => setTriggerType(e.target.value)}
                className="w-full text-xs p-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
              >
                {TRIGGER_OPTIONS.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Trạng thái vận hành
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="w-full text-xs p-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
              >
                <option value="ACTIVE">🟢 Đang hoạt động (ACTIVE)</option>
                <option value="PAUSED">⏸️ Tạm dừng (PAUSED)</option>
                <option value="DRAFT">📝 Bản nháp (DRAFT)</option>
              </select>
            </div>
          </div>

          {/* Conditions Builder */}
          <div className="border border-slate-200 rounded-xl p-4 bg-slate-50/50 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <span>🎯</span> Điều kiện kích hoạt (Conditions)
              </span>
              <button
                type="button"
                onClick={handleAddCondition}
                className="text-xs text-emerald-700 hover:text-emerald-800 font-semibold"
              >
                + Thêm điều kiện
              </button>
            </div>

            {conditions.length === 0 ? (
              <p className="text-xs text-slate-400 italic">Không có điều kiện (luôn thực thi khi sự kiện kích hoạt).</p>
            ) : (
              <div className="space-y-2">
                {conditions.map((cond, idx) => (
                  <div key={idx} className="flex items-center gap-2 bg-white p-2 rounded-lg border border-slate-200">
                    <input
                      type="text"
                      placeholder="Trường (vd: segment)"
                      value={cond.field}
                      onChange={(e) => handleUpdateCondition(idx, 'field', e.target.value)}
                      className="text-xs p-1.5 border border-slate-200 rounded flex-1 font-mono"
                    />
                    <select
                      value={cond.operator}
                      onChange={(e) => handleUpdateCondition(idx, 'operator', e.target.value)}
                      className="text-xs p-1.5 border border-slate-200 rounded bg-white font-mono"
                    >
                      <option value="eq">== (bằng)</option>
                      <option value="neq">!= (khác)</option>
                      <option value="gt">&gt; (lớn hơn)</option>
                      <option value="gte">&gt;= (lớn hơn bằng)</option>
                      <option value="lt">&lt; (nhỏ hơn)</option>
                      <option value="lte">&lt;= (nhỏ hơn bằng)</option>
                      <option value="in">in (thuộc danh sách)</option>
                      <option value="contains">contains (chứa ký tự)</option>
                    </select>
                    <input
                      type="text"
                      placeholder="Giá trị"
                      value={cond.value === undefined ? '' : String(cond.value)}
                      onChange={(e) => {
                        const val = e.target.value;
                        if (val === 'true') handleUpdateCondition(idx, 'value', true);
                        else if (val === 'false') handleUpdateCondition(idx, 'value', false);
                        else if (!isNaN(Number(val)) && val.trim() !== '') handleUpdateCondition(idx, 'value', Number(val));
                        else handleUpdateCondition(idx, 'value', val);
                      }}
                      className="text-xs p-1.5 border border-slate-200 rounded flex-1 font-mono"
                    />
                    <button
                      type="button"
                      onClick={() => handleRemoveCondition(idx)}
                      className="text-slate-400 hover:text-rose-500 p-1"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Actions Builder */}
          <div className="border border-slate-200 rounded-xl p-4 bg-slate-50/50 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <span>⚡</span> Chuỗi hành động thực thi (Actions)
              </span>
              <button
                type="button"
                onClick={handleAddAction}
                className="text-xs text-emerald-700 hover:text-emerald-800 font-semibold"
              >
                + Thêm hành động
              </button>
            </div>

            {actions.length === 0 ? (
              <p className="text-xs text-slate-400 italic">Vui lòng thêm ít nhất một hành động.</p>
            ) : (
              <div className="space-y-3">
                {actions.map((act, idx) => (
                  <div key={idx} className="bg-white p-3 rounded-xl border border-slate-200 space-y-2 relative">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-800">Bước {idx + 1}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveAction(idx)}
                        className="text-slate-400 hover:text-rose-500 text-xs"
                      >
                        ✕ Xóa bước
                      </button>
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-[11px] text-slate-500 mb-0.5">Loại hành động</label>
                        <select
                          value={act.type}
                          onChange={(e) => handleUpdateAction(idx, 'type', e.target.value)}
                          className="w-full text-xs p-1.5 border border-slate-200 rounded bg-white"
                        >
                          {ACTION_TYPE_OPTIONS.map((o) => (
                            <option key={o.value} value={o.value}>{o.label}</option>
                          ))}
                        </select>
                      </div>

                      {act.type === 'ISSUE_PROMOTION' && (
                        <div>
                          <label className="block text-[11px] text-slate-500 mb-0.5">Mã Voucher</label>
                          <input
                            type="text"
                            placeholder="vd: WELCOME20"
                            value={act.promotion_code || ''}
                            onChange={(e) => handleUpdateAction(idx, 'promotion_code', e.target.value.toUpperCase())}
                            className="w-full text-xs p-1.5 border border-slate-200 rounded font-mono"
                          />
                        </div>
                      )}

                      {act.type === 'ADD_LOYALTY_POINTS' && (
                        <div>
                          <label className="block text-[11px] text-slate-500 mb-0.5">Số điểm Mộc Xu</label>
                          <input
                            type="number"
                            placeholder="vd: 10"
                            value={act.points || 0}
                            onChange={(e) => handleUpdateAction(idx, 'points', Number(e.target.value))}
                            className="w-full text-xs p-1.5 border border-slate-200 rounded font-mono"
                          />
                        </div>
                      )}

                      {act.type === 'ADD_CUSTOMER_TAG' && (
                        <div>
                          <label className="block text-[11px] text-slate-500 mb-0.5">Thẻ phân loại (Tag)</label>
                          <input
                            type="text"
                            placeholder="vd: can_cham_soc_lai"
                            value={act.tag || ''}
                            onChange={(e) => handleUpdateAction(idx, 'tag', e.target.value)}
                            className="w-full text-xs p-1.5 border border-slate-200 rounded font-mono"
                          />
                        </div>
                      )}

                      {act.type === 'WAIT_HOURS' && (
                        <div>
                          <label className="block text-[11px] text-slate-500 mb-0.5">Thời gian chờ (Giờ)</label>
                          <input
                            type="number"
                            placeholder="vd: 2"
                            value={act.wait_hours || 2}
                            onChange={(e) => handleUpdateAction(idx, 'wait_hours', Number(e.target.value))}
                            className="w-full text-xs p-1.5 border border-slate-200 rounded font-mono"
                          />
                        </div>
                      )}
                    </div>

                    {(act.type === 'SEND_ZALO_MOCK' || act.type === 'SEND_EMAIL_MOCK') && (
                      <div>
                        <label className="block text-[11px] text-slate-500 mb-0.5">Nội dung tin nhắn</label>
                        <textarea
                          rows={2}
                          placeholder="Nội dung tin nhắn... Có thể dùng {customer_name}, {phone}"
                          value={act.message || ''}
                          onChange={(e) => handleUpdateAction(idx, 'message', e.target.value)}
                          className="w-full text-xs p-2 border border-slate-200 rounded"
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Modal Footer */}
          <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
            <Button variant="outline" size="sm" type="button" onClick={onClose}>
              Hủy bỏ
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={isLoading}>
              {workflow ? 'Lưu Thay Đổi' : 'Tạo Kịch Bản Mới'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
