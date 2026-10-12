'use client';

import React, { useState, useEffect } from 'react';
import { Dialog, Button, Input } from '@moc-healthy/ui';
import { inventoryApi, productsApi } from '../../lib/api';
import { Product, ProductListResponse } from '@moc-healthy/contracts';

interface ReceiveBatchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  initialProductId?: string;
}

export const ReceiveBatchModal: React.FC<ReceiveBatchModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  initialProductId,
}) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loadingProducts, setLoadingProducts] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form fields
  const [productId, setProductId] = useState(initialProductId || '');
  const [batchCode, setBatchCode] = useState('');
  const [quantityReceived, setQuantityReceived] = useState<number>(20);
  const [costPerUnit, setCostPerUnit] = useState<string>('');
  const [supplier, setSupplier] = useState('');
  const [expiryAt, setExpiryAt] = useState('');
  const [note, setNote] = useState('');

  // Default expiry date: 2 days from now for F&B
  useEffect(() => {
    if (isOpen) {
      const d = new Date();
      d.setDate(d.getDate() + 2);
      d.setMinutes(0);
      d.setSeconds(0);
      const isoStr = d.toISOString().slice(0, 16);
      setExpiryAt(isoStr);

      if (initialProductId) {
        setProductId(initialProductId);
      }
      setError(null);
    }
  }, [isOpen, initialProductId]);

  // Load products list for dropdown
  useEffect(() => {
    if (isOpen) {
      setLoadingProducts(true);
      productsApi
        .list({ page_size: 100 })
        .then((res: ProductListResponse) => {
          setProducts(res.items);
          if (!productId && res.items.length > 0) {
            setProductId(res.items[0].id);
          }
        })
        .catch((err) => {
          console.error('Failed to load products:', err);
        })
        .finally(() => setLoadingProducts(false));
    }
  }, [isOpen]);

  const selectedProduct = products.find((p) => p.id === productId);

  // If cost price exists on product, autofill
  useEffect(() => {
    if (selectedProduct && selectedProduct.cost_price && !costPerUnit) {
      setCostPerUnit(String(selectedProduct.cost_price));
    }
  }, [selectedProduct]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!productId) {
      setError('Vui lòng chọn sản phẩm nhập kho.');
      return;
    }
    if (!quantityReceived || quantityReceived <= 0) {
      setError('Số lượng nhập kho phải lớn hơn 0.');
      return;
    }
    if (!expiryAt) {
      setError('Vui lòng chọn ngày và giờ hết hạn.');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await inventoryApi.receiveBatch({
        product_id: productId,
        batch_code: batchCode.trim() || undefined,
        quantity_received: Number(quantityReceived),
        cost_per_unit: costPerUnit ? Number(costPerUnit) : undefined,
        supplier: supplier.trim() || undefined,
        expiry_at: new Date(expiryAt).toISOString(),
        note: note.trim() || undefined,
      });

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Lỗi khi nhập lô hàng.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog isOpen={isOpen} onClose={onClose} title="📥 Nhập Lô Hàng Mới (Receive Stock Batch)">
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg">
            {error}
          </div>
        )}

        {/* Product selector */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Sản phẩm F&B <span className="text-rose-500">*</span>
          </label>
          <select
            value={productId}
            onChange={(e) => setProductId(e.target.value)}
            disabled={loadingProducts || submitting}
            className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            {loadingProducts ? (
              <option value="">Đang tải danh sách sản phẩm...</option>
            ) : (
              products.map((p) => (
                <option key={p.id} value={p.id}>
                  [{p.sku}] {p.name} ({p.unit})
                </option>
              ))
            )}
          </select>
        </div>

        {/* Batch code & Supplier */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Mã lô (Tùy chọn)
            </label>
            <Input
              type="text"
              placeholder="Tự sinh: BATCH-YYYYMMDD-XXXX"
              value={batchCode}
              onChange={(e) => setBatchCode(e.target.value)}
              disabled={submitting}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Nhà cung cấp / Đối tác
            </label>
            <Input
              type="text"
              placeholder="Vd: Nông trại Đà Lạt, Bếp trung tâm..."
              value={supplier}
              onChange={(e) => setSupplier(e.target.value)}
              disabled={submitting}
            />
          </div>
        </div>

        {/* Quantity & Unit Cost */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Số lượng nhập ({selectedProduct?.unit || 'đơn vị'}) <span className="text-rose-500">*</span>
            </label>
            <Input
              type="number"
              min="1"
              value={quantityReceived}
              onChange={(e) => setQuantityReceived(Math.max(1, parseInt(e.target.value) || 0))}
              disabled={submitting}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Đơn giá vốn (VND/đơn vị)
            </label>
            <Input
              type="number"
              min="0"
              placeholder="25,000"
              value={costPerUnit}
              onChange={(e) => setCostPerUnit(e.target.value)}
              disabled={submitting}
            />
          </div>
        </div>

        {/* Expiry Date */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Hạn sử dụng (Expiry Date & Time) <span className="text-rose-500">*</span>
          </label>
          <Input
            type="datetime-local"
            value={expiryAt}
            onChange={(e) => setExpiryAt(e.target.value)}
            disabled={submitting}
          />
          <p className="text-[11px] text-slate-500 mt-1">
            💡 Lưu ý đặc thù F&B: Đồ uống ép chậm và trái cây tươi thường có HSD từ 24h - 48h.
          </p>
        </div>

        {/* Note */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Ghi chú nhập kho
          </label>
          <textarea
            rows={2}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Ghi chú về chất lượng hoặc chứng từ..."
            className="w-full text-xs rounded-lg border border-slate-300 px-3 py-2 bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            disabled={submitting}
          />
        </div>

        <div className="flex justify-end space-x-2 pt-3 border-t border-slate-100">
          <Button type="button" variant="ghost" onClick={onClose} disabled={submitting}>
            Hủy bỏ
          </Button>
          <Button type="submit" variant="primary" isLoading={submitting}>
            Xác nhận nhập kho
          </Button>
        </div>
      </form>
    </Dialog>
  );
};
