'use client';

import React, { useState, useEffect } from 'react';
import { Dialog, Button, Input, Badge } from '@moc-healthy/ui';
import { inventoryApi, productsApi } from '../../lib/api';
import { Product, ProductListResponse, FefoAllocationResult } from '@moc-healthy/contracts';

interface FefoSimulatorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  initialProductId?: string;
}

export const FefoSimulatorModal: React.FC<FefoSimulatorModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  initialProductId,
}) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [productId, setProductId] = useState(initialProductId || '');
  const [quantity, setQuantity] = useState<number>(10);
  const [referenceId, setReferenceId] = useState<string>('ORDER-DEMO-001');

  const [simulating, setSimulating] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [result, setResult] = useState<FefoAllocationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [executeSuccess, setExecuteSuccess] = useState<boolean>(false);

  useEffect(() => {
    if (isOpen) {
      productsApi.list({ page_size: 100 }).then((res: ProductListResponse) => {
        setProducts(res.items);
        if (!productId && res.items.length > 0) {
          setProductId(res.items[0].id);
        }
      });
      setError(null);
      setResult(null);
      setExecuteSuccess(false);
    }
  }, [isOpen]);

  const handleSimulate = async () => {
    if (!productId || quantity <= 0) {
      setError('Vui lòng chọn sản phẩm và số lượng hợp lệ.');
      return;
    }

    setSimulating(true);
    setError(null);
    setExecuteSuccess(false);

    try {
      const res = await inventoryApi.simulateFefo({
        product_id: productId,
        quantity: Number(quantity),
        reference_id: referenceId.trim() || undefined,
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Lỗi khi mô phỏng phân bổ FEFO.');
      setResult(null);
    } finally {
      setSimulating(false);
    }
  };

  const handleExecute = async () => {
    if (!productId || quantity <= 0) return;
    if (!window.confirm(`Bạn có chắc muốn thực thi xuất kho ${quantity} đơn vị theo thuật toán FEFO?`)) {
      return;
    }

    setExecuting(true);
    setError(null);

    try {
      const res = await inventoryApi.allocateFefo({
        product_id: productId,
        quantity: Number(quantity),
        reference_id: referenceId.trim() || undefined,
        note: 'Xuất kho phân bổ theo thuật toán FEFO từ màn hình quản trị',
      });
      setResult(res);
      setExecuteSuccess(true);
      onSuccess();
    } catch (err: any) {
      setError(err.message || 'Lỗi khi thực thi xuất kho FEFO.');
    } finally {
      setExecuting(false);
    }
  };

  return (
    <Dialog isOpen={isOpen} onClose={onClose} title="⚡ Thuật Toán Phân Bổ FEFO (First Expired, First Out)">
      <div className="space-y-4">
        <p className="text-xs text-slate-600">
          Mô phỏng cơ chế tự động ưu tiên xuất kho các lô hàng F&B có <strong>hạn sử dụng gần nhất trước</strong> để giảm thiểu tối đa tỷ lệ hủy hỏng (waste).
        </p>

        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg">
            {error}
          </div>
        )}

        {executeSuccess && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs rounded-lg font-medium">
            ✅ Đã thực thi xuất kho thành công! Các dòng movement SALE_OUT đã được lưu vào sổ cái.
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Sản phẩm cần xuất
            </label>
            <select
              value={productId}
              onChange={(e) => {
                setProductId(e.target.value);
                setResult(null);
              }}
              className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  [{p.sku}] {p.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Số lượng xuất yêu cầu
            </label>
            <Input
              type="number"
              min="1"
              value={quantity}
              onChange={(e) => {
                setQuantity(Math.max(1, parseInt(e.target.value) || 0));
                setResult(null);
              }}
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Mã đơn hàng / Tham chiếu xuất
          </label>
          <Input
            type="text"
            placeholder="ORDER-2026-001"
            value={referenceId}
            onChange={(e) => setReferenceId(e.target.value)}
          />
        </div>

        <div className="flex justify-start space-x-2 pt-2">
          <Button
            type="button"
            variant="secondary"
            isLoading={simulating}
            onClick={handleSimulate}
          >
            🔍 Mô phỏng phân bổ (Dry Run)
          </Button>

          {result && !executeSuccess && (
            <Button
              type="button"
              variant="primary"
              isLoading={executing}
              onClick={handleExecute}
            >
              🚀 Thực thi xuất kho thực tế (SALE_OUT)
            </Button>
          )}
        </div>

        {/* Result Table */}
        {result && (
          <div className="mt-4 pt-4 border-t border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-800">
                Kết quả phân bổ: {result.product_name}
              </span>
              <Badge variant={result.is_fully_allocated ? 'success' : 'warning'}>
                {result.is_fully_allocated ? 'Đủ hàng 100%' : 'Thiếu hàng'}
              </Badge>
            </div>

            <div className="overflow-x-auto border border-slate-200 rounded-lg">
              <table className="min-w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="px-3 py-2">Thứ tự FEFO</th>
                    <th className="px-3 py-2">Mã lô</th>
                    <th className="px-3 py-2">Hạn sử dụng</th>
                    <th className="px-3 py-2">Tồn trước</th>
                    <th className="px-3 py-2 text-emerald-700 font-bold">Lấy xuất</th>
                    <th className="px-3 py-2">Tồn sau</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {result.allocations.map((a, idx) => (
                    <tr key={a.batch_id} className="hover:bg-slate-50">
                      <td className="px-3 py-2 font-mono font-bold text-slate-500">#{idx + 1}</td>
                      <td className="px-3 py-2 font-mono font-semibold text-slate-800">{a.batch_code}</td>
                      <td className="px-3 py-2 text-slate-600">
                        {new Date(a.expiry_at).toLocaleString('vi-VN')}
                      </td>
                      <td className="px-3 py-2 text-slate-500">{a.quantity_before}</td>
                      <td className="px-3 py-2 font-bold text-emerald-700">-{a.allocated_quantity}</td>
                      <td className="px-3 py-2 text-slate-700 font-medium">{a.quantity_after}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div className="flex justify-end pt-3 border-t border-slate-100">
          <Button variant="ghost" onClick={onClose}>
            Đóng
          </Button>
        </div>
      </div>
    </Dialog>
  );
};
