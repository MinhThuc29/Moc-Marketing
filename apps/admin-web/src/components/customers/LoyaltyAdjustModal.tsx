'use client';

import React, { useState } from 'react';
import {
  Dialog,
  Button,
  Input,
} from '@moc-healthy/ui';
import { customersApi } from '../../lib/api';

export interface LoyaltyAdjustModalProps {
  isOpen: boolean;
  onClose: () => void;
  customerId: string;
  customerName: string;
  currentPoints: number;
  onSuccess: () => void;
}

export const LoyaltyAdjustModal: React.FC<LoyaltyAdjustModalProps> = ({
  isOpen,
  onClose,
  customerId,
  customerName,
  currentPoints,
  onSuccess,
}) => {
  const [pointsDelta, setPointsDelta] = useState<number>(10);
  const [actionType, setActionType] = useState<'ADD' | 'DEDUCT'>('ADD');
  const [reason, setReason] = useState('Thưởng điểm tri ân khách hàng thân thiết');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reason.trim()) {
      setErrorMessage('Vui lòng nhập lý do điều chỉnh điểm');
      return;
    }
    const delta = actionType === 'ADD' ? Math.abs(pointsDelta) : -Math.abs(pointsDelta);
    if (actionType === 'DEDUCT' && Math.abs(pointsDelta) > currentPoints) {
      setErrorMessage(`Không thể trừ vượt quá số dư hiện tại (${currentPoints} Mộc Xu)`);
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      await customersApi.adjustLoyalty(customerId, {
        points: delta,
        reason: reason.trim(),
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setErrorMessage(err.message || 'Lỗi khi điều chỉnh điểm');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="🪙 Điều chỉnh điểm thưởng Mộc Xu"
      maxWidth="md"
    >
      <form onSubmit={handleSubmit} className="space-y-4 text-xs text-slate-700">
        {errorMessage && (
          <div className="p-2.5 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg">
            {errorMessage}
          </div>
        )}

        <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl flex items-center justify-between">
          <div>
            <p className="text-[11px] text-amber-800 font-medium">Khách hàng:</p>
            <p className="text-sm font-bold text-amber-950">{customerName}</p>
          </div>
          <div className="text-right">
            <p className="text-[11px] text-amber-800 font-medium">Số dư hiện tại:</p>
            <p className="text-base font-extrabold text-amber-900 font-mono">
              {currentPoints.toLocaleString('vi-VN')} <span className="text-xs">Mộc Xu</span>
            </p>
          </div>
        </div>

        {/* Action Type Toggle */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5">
            Loại thao tác:
          </label>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              className={`py-2 px-3 rounded-lg border text-xs font-semibold transition-all ${
                actionType === 'ADD'
                  ? 'bg-emerald-600 text-white border-emerald-600 shadow-xs'
                  : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
              }`}
              onClick={() => {
                setActionType('ADD');
                setReason('Thưởng điểm tri ân khách hàng thân thiết');
              }}
            >
              ➕ Cộng thêm điểm
            </button>
            <button
              type="button"
              className={`py-2 px-3 rounded-lg border text-xs font-semibold transition-all ${
                actionType === 'DEDUCT'
                  ? 'bg-rose-600 text-white border-rose-600 shadow-xs'
                  : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
              }`}
              onClick={() => {
                setActionType('DEDUCT');
                setReason('Đổi voucher ưu đãi hoặc điều chỉnh giảm');
              }}
            >
              ➖ Trừ bớt điểm
            </button>
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Số điểm Mộc Xu ({actionType === 'ADD' ? 'cộng vào' : 'trừ đi'}):
          </label>
          <Input
            type="number"
            min={1}
            max={actionType === 'DEDUCT' ? currentPoints : 100000}
            value={pointsDelta}
            onChange={(e) => setPointsDelta(Math.max(1, parseInt(e.target.value) || 0))}
            required
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Lý do điều chỉnh (Kiểm toán & Lịch sử) <span className="text-rose-500">*</span>:
          </label>
          <Input
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Ví dụ: Tặng quà sinh nhật thành viên VIP"
            required
          />
        </div>

        <div className="flex justify-end gap-2 pt-3 border-t border-slate-200">
          <Button type="button" variant="outline" size="sm" onClick={onClose} disabled={isSubmitting}>
            Hủy
          </Button>
          <Button type="submit" variant="primary" size="sm" disabled={isSubmitting}>
            {isSubmitting ? 'Đang xử lý...' : 'Xác nhận điều chỉnh'}
          </Button>
        </div>
      </form>
    </Dialog>
  );
};
