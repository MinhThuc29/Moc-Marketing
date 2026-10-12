'use client';

import React, { useState, useEffect } from 'react';
import { Dialog, Button, Badge, Skeleton, EmptyState } from '@moc-healthy/ui';
import { Product, PriceAuditLog } from '@moc-healthy/contracts';
import { productsApi } from '../../lib/api';

interface PriceHistoryDialogProps {
  isOpen: boolean;
  onClose: () => void;
  product: Product | null;
}

export const PriceHistoryDialog: React.FC<PriceHistoryDialogProps> = ({
  isOpen,
  onClose,
  product,
}) => {
  const [logs, setLogs] = useState<PriceAuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && product) {
      loadHistory(product.id);
    } else {
      setLogs([]);
      setErrorMessage(null);
    }
  }, [isOpen, product]);

  const loadHistory = async (productId: string) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await productsApi.getPriceHistory(productId);
      setLogs(data);
    } catch (err: any) {
      setErrorMessage(err.message || 'Không thể tải lịch sử giá');
    } finally {
      setIsLoading(false);
    }
  };

  const formatVND = (val?: number | null) => {
    if (val === null || val === undefined) return '—';
    return `${Number(val).toLocaleString('vi-VN')} đ`;
  };

  const formatDate = (iso: string) => {
    try {
      const d = new Date(iso);
      return d.toLocaleString('vi-VN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return iso;
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title={`Lịch sử kiểm toán giá: ${product?.name || ''}`}
      maxWidth="lg"
      footer={
        <Button variant="secondary" onClick={onClose}>
          Đóng
        </Button>
      }
    >
      <div className="space-y-4">
        {product && (
          <div className="flex items-center justify-between p-3 bg-slate-50 border border-slate-200/70 rounded-lg text-sm">
            <div>
              <span className="text-slate-500">Mã SKU:</span>{' '}
              <strong className="font-mono text-slate-800">{product.sku}</strong>
            </div>
            <div>
              <span className="text-slate-500">Giá hiện tại:</span>{' '}
              <strong className="text-emerald-700">{formatVND(product.base_price)}</strong>
              {product.sale_price && (
                <span className="ml-2 text-rose-600 font-semibold">
                  (Khuyến mãi: {formatVND(product.sale_price)})
                </span>
              )}
            </div>
          </div>
        )}

        {errorMessage && (
          <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg border border-red-200">
            {errorMessage}
          </div>
        )}

        {isLoading ? (
          <div className="space-y-3 py-4">
            <Skeleton height="50px" />
            <Skeleton height="50px" />
            <Skeleton height="50px" />
          </div>
        ) : logs.length === 0 ? (
          <EmptyState
            title="Chưa có bản ghi biến động giá"
            description="Lịch sử giá sẽ được tự động ghi lại mỗi khi giá niêm yết hoặc giá khuyến mãi được cập nhật."
            icon="🏷️"
          />
        ) : (
          <div className="overflow-x-auto border border-slate-200 rounded-lg">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase">
                <tr>
                  <th className="px-4 py-3">Thời gian</th>
                  <th className="px-4 py-3">Giá niêm yết</th>
                  <th className="px-4 py-3">Giá khuyến mãi</th>
                  <th className="px-4 py-3">Lý do thay đổi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {logs.map((log) => {
                  const baseChanged = log.old_base_price !== null && log.old_base_price !== log.new_base_price;
                  const saleChanged = log.old_sale_price !== null && log.old_sale_price !== log.new_sale_price;

                  return (
                    <tr key={log.id} className="hover:bg-slate-50/50">
                      <td className="px-4 py-3 text-xs text-slate-500 whitespace-nowrap">
                        {formatDate(log.created_at)}
                      </td>
                      <td className="px-4 py-3">
                        {log.old_base_price !== null ? (
                          <div className="flex items-center gap-1.5">
                            <span className="line-through text-slate-400 text-xs">
                              {formatVND(log.old_base_price)}
                            </span>
                            <span className="text-slate-400">→</span>
                            <span className={`font-semibold ${baseChanged ? 'text-emerald-700' : 'text-slate-800'}`}>
                              {formatVND(log.new_base_price)}
                            </span>
                          </div>
                        ) : (
                          <span className="font-semibold text-emerald-700">
                            {formatVND(log.new_base_price)}{' '}
                            <Badge variant="success">Khởi tạo</Badge>
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {log.old_sale_price !== null || log.new_sale_price !== null ? (
                          <div className="flex items-center gap-1.5">
                            {log.old_sale_price !== null && (
                              <span className="line-through text-slate-400 text-xs">
                                {formatVND(log.old_sale_price)}
                              </span>
                            )}
                            {log.old_sale_price !== null && <span className="text-slate-400">→</span>}
                            <span className={`font-semibold ${saleChanged ? 'text-rose-600' : 'text-slate-600'}`}>
                              {formatVND(log.new_sale_price)}
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-400 text-xs">Không áp dụng</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-700">
                        {log.change_reason || (
                          <span className="text-slate-400 italic">Không có ghi chú</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Dialog>
  );
};
