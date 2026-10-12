'use client';

import React, { useState, useEffect } from 'react';
import { Dialog, Button, Input } from '@moc-healthy/ui';
import { inventoryApi } from '../../lib/api';
import { InventoryBatch } from '@moc-healthy/contracts';

interface AdjustStockModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  batch: InventoryBatch | null;
}

export const AdjustStockModal: React.FC<AdjustStockModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  batch,
}) => {
  const [movementType, setMovementType] = useState<string>('WASTE_OUT');
  const [quantity, setQuantity] = useState<number>(1);
  const [reason, setReason] = useState<string>('Hết hạn sử dụng');
  const [customReason, setCustomReason] = useState<string>('');
  const [referenceId, setReferenceId] = useState<string>('');
  const [note, setNote] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setError(null);
      setQuantity(1);
      setNote('');
      setReferenceId('');
      if (batch?.is_expired) {
        setMovementType('WASTE_OUT');
        setReason('Hết hạn sử dụng');
      } else {
        setMovementType('ADJUSTMENT_OUT');
        setReason('Kiểm kê định kỳ phát hiện thiếu');
      }
    }
  }, [isOpen, batch]);

  if (!batch) return null;

  const isOutMovement = movementType === 'ADJUSTMENT_OUT' || movementType === 'WASTE_OUT';

  const reasonPresets: Record<string, string[]> = {
    WASTE_OUT: [
      'Hết hạn sử dụng (Quá hạn F&B)',
      'Trái cây bị dập nát / hư hỏng bảo quản',
      'Đồ uống bị chua / hỏng hương vị',
      'Lỗi đóng chai / bao bì rách thủng',
    ],
    ADJUSTMENT_OUT: [
      'Kiểm kê định kỳ phát hiện thiếu',
      'Hao hụt tự nhiên trong quá trình cắt gọt',
      'Xuất mẫu thử nghiệm chất lượng (QC)',
    ],
    ADJUSTMENT_IN: [
      'Kiểm kê định kỳ phát hiện dư',
      'Nhập bù từ nguồn sơ chế phụ',
      'Điều chỉnh sai sót số liệu lần nhập trước',
    ],
    RETURN_IN: [
      'Khách hủy đơn hoàn trả hàng nguyên vẹn',
      'Hoàn trả hàng bảo quản lạnh an toàn',
    ],
  };

  const currentPresets = reasonPresets[movementType] || [];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!quantity || quantity <= 0) {
      setError('Số lượng điều chỉnh phải lớn hơn 0.');
      return;
    }

    if (isOutMovement && quantity > batch.quantity_available) {
      setError(
        `Số lượng xuất/giảm (${quantity}) không được vượt quá số lượng tồn khả dụng (${batch.quantity_available}) của lô.`
      );
      return;
    }

    const finalReason = reason === 'OTHER' ? customReason.trim() : reason;
    if (!finalReason) {
      setError('Vui lòng cung cấp lý do điều chỉnh kho.');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await inventoryApi.adjustStock({
        batch_id: batch.id,
        movement_type: movementType,
        quantity: Number(quantity),
        reason: finalReason,
        reference_id: referenceId.trim() || undefined,
        note: note.trim() || undefined,
      });

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Lỗi khi cập nhật kho.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog isOpen={isOpen} onClose={onClose} title="⚖️ Điều Chỉnh Tồn Kho / Xuất Hủy (Stock Adjustment)">
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg">
            {error}
          </div>
        )}

        {/* Batch Preview Card */}
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
          <div className="flex justify-between font-bold text-slate-800">
            <span>Mã lô: {batch.batch_code}</span>
            <span className="text-emerald-700">
              Tồn hiện tại: {batch.quantity_available} {batch.product_unit || 'đơn vị'}
            </span>
          </div>
          <div className="text-slate-600">
            Sản phẩm: {batch.product_name} ({batch.product_sku})
          </div>
          <div className="text-slate-500 text-[11px]">
            HSD: {new Date(batch.expiry_at).toLocaleString('vi-VN')}
            {batch.is_expired ? (
              <span className="ml-2 font-bold text-rose-600">(Đã quá hạn)</span>
            ) : batch.is_critical ? (
              <span className="ml-2 font-bold text-amber-600">(Cận date &lt; 24h)</span>
            ) : null}
          </div>
        </div>

        {/* Movement Type */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Loại giao dịch điều chỉnh <span className="text-rose-500">*</span>
          </label>
          <select
            value={movementType}
            onChange={(e) => {
              setMovementType(e.target.value);
              const presets = reasonPresets[e.target.value] || [];
              if (presets.length > 0) setReason(presets[0]);
            }}
            disabled={submitting}
            className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="WASTE_OUT">🔴 Xuất hủy hỏng / Hết hạn (WASTE_OUT)</option>
            <option value="ADJUSTMENT_OUT">🟠 Điều chỉnh giảm kiểm kê thiếu (ADJUSTMENT_OUT)</option>
            <option value="ADJUSTMENT_IN">🟢 Điều chỉnh tăng kiểm kê thừa (ADJUSTMENT_IN)</option>
            <option value="RETURN_IN">🔵 Nhập hoàn trả hàng (RETURN_IN)</option>
          </select>
        </div>

        {/* Quantity */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Số lượng điều chỉnh ({batch.product_unit || 'đơn vị'}) <span className="text-rose-500">*</span>
          </label>
          <Input
            type="number"
            min="1"
            max={isOutMovement ? batch.quantity_available : undefined}
            value={quantity}
            onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 0))}
            disabled={submitting}
          />
          {isOutMovement && (
            <p className="text-[11px] text-slate-500 mt-1">
              Tối đa có thể xuất: {batch.quantity_available} {batch.product_unit || 'đơn vị'}
            </p>
          )}
        </div>

        {/* Reason Presets */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Lý do điều chỉnh <span className="text-rose-500">*</span>
          </label>
          <select
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            disabled={submitting}
            className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 mb-2"
          >
            {currentPresets.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
            <option value="OTHER">Lý do khác...</option>
          </select>

          {reason === 'OTHER' && (
            <Input
              type="text"
              placeholder="Nhập lý do cụ thể..."
              value={customReason}
              onChange={(e) => setCustomReason(e.target.value)}
              disabled={submitting}
            />
          )}
        </div>

        {/* Reference ID & Note */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Mã tham chiếu (Tùy chọn)
            </label>
            <Input
              type="text"
              placeholder="Vd: BIEN-BAN-HUY-01"
              value={referenceId}
              onChange={(e) => setReferenceId(e.target.value)}
              disabled={submitting}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Ghi chú thêm
            </label>
            <Input
              type="text"
              placeholder="Ghi chú chi tiết..."
              value={note}
              onChange={(e) => setNote(e.target.value)}
              disabled={submitting}
            />
          </div>
        </div>

        <div className="flex justify-end space-x-2 pt-3 border-t border-slate-100">
          <Button type="button" variant="ghost" onClick={onClose} disabled={submitting}>
            Hủy bỏ
          </Button>
          <Button
            type="submit"
            variant={movementType === 'WASTE_OUT' ? 'danger' : 'primary'}
            isLoading={submitting}
          >
            Xác nhận điều chỉnh
          </Button>
        </div>
      </form>
    </Dialog>
  );
};
