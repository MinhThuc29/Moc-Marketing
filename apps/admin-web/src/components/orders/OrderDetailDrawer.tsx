'use client';

import React, { useState, useEffect } from 'react';
import {
  Drawer,
  Dialog,
  Button,
  Badge,
  Input,
} from '@moc-healthy/ui';
import {
  AdminOrderDetail,
  OrderStatus,
  PaymentStatus,
} from '@moc-healthy/contracts';
import { ordersApi } from '../../lib/api';

export interface OrderDetailDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  orderId: string | null;
  onOrderUpdated: () => void;
}

const STATUS_LABELS: Record<OrderStatus, { text: string; variant: 'neutral' | 'success' | 'warning' | 'danger' | 'info' }> = {
  NEW: { text: 'Mới (Chờ duyệt)', variant: 'warning' },
  CONFIRMED: { text: 'Đã xác nhận', variant: 'info' },
  PREPARING: { text: 'Đang làm món', variant: 'warning' },
  READY: { text: 'Món sẵn sàng', variant: 'info' },
  SHIPPING: { text: 'Đang giao hàng', variant: 'info' },
  COMPLETED: { text: 'Hoàn thành', variant: 'success' },
  CANCELLED: { text: 'Đã hủy', variant: 'danger' },
  REFUNDED: { text: 'Đã hoàn tiền', variant: 'neutral' },
};

const PAYMENT_STATUS_LABELS: Record<PaymentStatus, { text: string; variant: 'neutral' | 'success' | 'warning' | 'danger' | 'info' }> = {
  PENDING: { text: 'Chưa thanh toán', variant: 'warning' },
  PAID: { text: 'Đã thanh toán', variant: 'success' },
  FAILED: { text: 'Thất bại', variant: 'danger' },
  REFUNDED: { text: 'Đã hoàn tiền', variant: 'neutral' },
};

const SOURCE_LABELS: Record<string, string> = {
  ONLINE: 'Website Online',
  PHONE: 'Hotline / Điện thoại',
  WALK_IN: 'Mua tại quầy',
  ZALO: 'Zalo OA',
  FACEBOOK: 'Facebook Messenger',
};

export const OrderDetailDrawer: React.FC<OrderDetailDrawerProps> = ({
  isOpen,
  onClose,
  orderId,
  onOrderUpdated,
}) => {
  const [order, setOrder] = useState<AdminOrderDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Internal note editing
  const [internalNote, setInternalNote] = useState('');
  const [savingNote, setSavingNote] = useState(false);

  // Cancel order modal
  const [isCancelModalOpen, setIsCancelModalOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState('Khách hàng yêu cầu hủy đơn');

  // Load detail
  useEffect(() => {
    if (!isOpen || !orderId) {
      setOrder(null);
      setErrorMessage(null);
      setSuccessMessage(null);
      return;
    }

    const fetchDetail = async () => {
      setIsLoading(true);
      setErrorMessage(null);
      try {
        const data = await ordersApi.getDetail(orderId);
        setOrder(data);
        setInternalNote(data.internal_note || '');
      } catch (err: any) {
        setErrorMessage(err.message || 'Không thể tải chi tiết đơn hàng');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDetail();
  }, [isOpen, orderId]);

  const handleStatusTransition = async (newStatus: OrderStatus, reason?: string) => {
    if (!order) return;
    setActionLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      const updated = await ordersApi.updateStatus(order.id, {
        new_status: newStatus,
        reason: reason || undefined,
      });
      setOrder(updated);
      setSuccessMessage(`Đã cập nhật trạng thái sang "${STATUS_LABELS[newStatus]?.text}"`);
      onOrderUpdated();
    } catch (err: any) {
      setErrorMessage(err.message || 'Chuyển trạng thái thất bại');
    } finally {
      setActionLoading(false);
    }
  };

  const handlePaymentStatusChange = async (newPayStatus: PaymentStatus) => {
    if (!order) return;
    setActionLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      const updated = await ordersApi.updatePaymentStatus(order.id, {
        payment_status: newPayStatus,
        note: `Cập nhật thủ công bởi quản trị viên lúc ${new Date().toLocaleTimeString('vi-VN')}`,
      });
      setOrder(updated);
      setSuccessMessage(`Đã cập nhật thanh toán thành "${PAYMENT_STATUS_LABELS[newPayStatus]?.text}"`);
      onOrderUpdated();
    } catch (err: any) {
      setErrorMessage(err.message || 'Cập nhật trạng thái thanh toán thất bại');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSaveInternalNote = async () => {
    if (!order) return;
    setSavingNote(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      const updated = await ordersApi.updateInternalNote(order.id, {
        internal_note: internalNote,
      });
      setOrder(updated);
      setSuccessMessage('Đã lưu ghi chú nội bộ');
      onOrderUpdated();
    } catch (err: any) {
      setErrorMessage(err.message || 'Không thể lưu ghi chú nội bộ');
    } finally {
      setSavingNote(false);
    }
  };

  const handleConfirmCancel = async () => {
    setIsCancelModalOpen(false);
    await handleStatusTransition('CANCELLED', cancelReason);
  };

  if (!isOpen) return null;

  return (
    <Drawer
      isOpen={isOpen}
      onClose={onClose}
      maxWidth="xl"
      title={order ? `Chi tiết đơn #${order.order_number}` : 'Chi tiết đơn hàng'}
      footer={
        <div className="flex items-center justify-between w-full">
          <span className="text-xs text-slate-400">
            {order ? `Cập nhật lúc: ${new Date(order.updated_at).toLocaleString('vi-VN')}` : ''}
          </span>
          <Button variant="outline" size="sm" onClick={onClose}>
            Đóng
          </Button>
        </div>
      }
    >
      {isLoading ? (
        <div className="py-12 flex flex-col items-center justify-center space-y-3">
          <div className="w-8 h-8 border-3 border-emerald-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-slate-500">Đang tải dữ liệu đơn hàng...</p>
        </div>
      ) : errorMessage && !order ? (
        <div className="p-4 bg-red-50 text-red-700 text-sm rounded-lg border border-red-200">
          {errorMessage}
        </div>
      ) : order ? (
        <div className="space-y-6 text-sm text-slate-700">
          {/* Notifications */}
          {errorMessage && (
            <div className="p-3 bg-red-50 text-red-700 text-xs rounded-lg border border-red-200">
              {errorMessage}
            </div>
          )}
          {successMessage && (
            <div className="p-3 bg-emerald-50 text-emerald-800 text-xs rounded-lg border border-emerald-200">
              {successMessage}
            </div>
          )}

          {/* 1. Header Overview & Status Bar */}
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200/80 space-y-3">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div>
                <span className="text-xs text-slate-500 block">Mã đơn hàng</span>
                <span className="text-lg font-bold text-slate-900 tracking-tight">#{order.order_number}</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={STATUS_LABELS[order.status]?.variant || 'neutral'} size="md">
                  {STATUS_LABELS[order.status]?.text || order.status}
                </Badge>
                <Badge variant={PAYMENT_STATUS_LABELS[order.payment_status]?.variant || 'neutral'} size="md">
                  {PAYMENT_STATUS_LABELS[order.payment_status]?.text || order.payment_status}
                </Badge>
              </div>
            </div>

            <div className="text-xs text-slate-500 flex flex-wrap gap-x-4 gap-y-1 pt-1 border-t border-slate-200/60">
              <span>Ngày đặt: <strong>{new Date(order.created_at).toLocaleString('vi-VN')}</strong></span>
              <span>Kênh: <strong>{SOURCE_LABELS[order.source] || order.source}</strong></span>
              <span>PTTT: <strong>{order.payment_method === 'COD' ? 'Tiền mặt khi nhận (COD)' : 'Chuyển khoản VietQR'}</strong></span>
            </div>
          </div>

          {/* 2. State Machine Action Buttons */}
          <div className="p-4 bg-white rounded-xl border border-emerald-100 shadow-xs space-y-3">
            <h4 className="text-xs font-semibold text-emerald-950 uppercase tracking-wider">
              Thao tác chuyển trạng thái đơn hàng
            </h4>

            <div className="flex flex-wrap gap-2">
              {order.status === 'NEW' && (
                <>
                  <Button
                    size="sm"
                    variant="primary"
                    isLoading={actionLoading}
                    onClick={() => handleStatusTransition('CONFIRMED', 'Admin xác nhận đơn')}
                  >
                    ✓ Xác nhận đơn hàng
                  </Button>
                  <Button
                    size="sm"
                    variant="danger"
                    disabled={actionLoading}
                    onClick={() => setIsCancelModalOpen(true)}
                  >
                    ✕ Hủy đơn
                  </Button>
                </>
              )}

              {order.status === 'CONFIRMED' && (
                <>
                  <Button
                    size="sm"
                    variant="primary"
                    isLoading={actionLoading}
                    onClick={() => handleStatusTransition('PREPARING', 'Bếp bắt đầu chế biến')}
                  >
                    🍳 Bắt đầu làm món
                  </Button>
                  <Button
                    size="sm"
                    variant="danger"
                    disabled={actionLoading}
                    onClick={() => setIsCancelModalOpen(true)}
                  >
                    ✕ Hủy đơn
                  </Button>
                </>
              )}

              {order.status === 'PREPARING' && (
                <>
                  <Button
                    size="sm"
                    variant="primary"
                    isLoading={actionLoading}
                    onClick={() => handleStatusTransition('READY', 'Món ăn đã đóng hộp hoàn tất')}
                  >
                    📦 Món đã sẵn sàng giao
                  </Button>
                  <Button
                    size="sm"
                    variant="danger"
                    disabled={actionLoading}
                    onClick={() => setIsCancelModalOpen(true)}
                  >
                    ✕ Hủy đơn
                  </Button>
                </>
              )}

              {order.status === 'READY' && (
                <>
                  <Button
                    size="sm"
                    variant="primary"
                    isLoading={actionLoading}
                    onClick={() => handleStatusTransition('SHIPPING', 'Bàn giao shipper đi giao')}
                  >
                    🛵 Bắt đầu giao hàng
                  </Button>
                  <Button
                    size="sm"
                    variant="danger"
                    disabled={actionLoading}
                    onClick={() => setIsCancelModalOpen(true)}
                  >
                    ✕ Hủy đơn
                  </Button>
                </>
              )}

              {order.status === 'SHIPPING' && (
                <>
                  <Button
                    size="sm"
                    variant="primary"
                    isLoading={actionLoading}
                    onClick={() => handleStatusTransition('COMPLETED', 'Khách đã nhận hàng thành công')}
                  >
                    🎉 Hoàn thành đơn hàng
                  </Button>
                  <Button
                    size="sm"
                    variant="danger"
                    disabled={actionLoading}
                    onClick={() => setIsCancelModalOpen(true)}
                  >
                    ✕ Hủy đơn (Giao không thành công)
                  </Button>
                </>
              )}

              {order.status === 'COMPLETED' && (
                <Button
                  size="sm"
                  variant="outline"
                  isLoading={actionLoading}
                  onClick={() => handleStatusTransition('REFUNDED', 'Hoàn tiền theo khiếu nại của khách')}
                >
                  ↩ Hoàn tiền đơn hàng (Refund)
                </Button>
              )}

              {(order.status === 'CANCELLED' || order.status === 'REFUNDED') && (
                <div className="text-xs text-slate-500 italic py-1">
                  Đơn hàng đã kết thúc chu kỳ xử lý ({order.status === 'CANCELLED' ? 'Đã hủy & hoàn tồn kho' : 'Đã hoàn tiền'}).
                </div>
              )}
            </div>
          </div>

          {/* 3. Customer & Shipping Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-slate-50/60 rounded-xl border border-slate-200/80 space-y-2">
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Khách hàng
              </h4>
              <div className="text-xs space-y-1">
                <p className="font-semibold text-slate-900 text-sm">{order.customer_name}</p>
                <p className="text-slate-600 flex items-center gap-1">
                  📞 <a href={`tel:${order.customer_phone}`} className="text-emerald-700 hover:underline font-mono">{order.customer_phone}</a>
                </p>
                {order.customer_email && (
                  <p className="text-slate-500">✉ {order.customer_email}</p>
                )}
              </div>
            </div>

            <div className="p-4 bg-slate-50/60 rounded-xl border border-slate-200/80 space-y-2">
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Địa chỉ giao hàng
              </h4>
              <div className="text-xs space-y-1">
                <p className="text-slate-800 leading-relaxed">{order.delivery_address}</p>
                {order.customer_note && (
                  <div className="mt-2 p-2 bg-amber-50 rounded border border-amber-200 text-amber-900 text-[11px]">
                    <strong>Ghi chú của khách:</strong> {order.customer_note}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* 4. Line Items */}
          <div className="border border-slate-200 rounded-xl overflow-hidden">
            <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 font-semibold text-xs text-slate-800 flex justify-between">
              <span>Sản phẩm ({order.items.length} món)</span>
              <span>Thành tiền</span>
            </div>
            <div className="divide-y divide-slate-100">
              {order.items.map((it) => (
                <div key={it.id} className="p-4 flex items-center justify-between gap-3 text-xs">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold text-sm shrink-0">
                      🥗
                    </div>
                    <div>
                      <p className="font-semibold text-slate-900">{it.product_name}</p>
                      <p className="text-[11px] text-slate-400">
                        SKU: {it.product_sku} | {it.product_unit} | Đơn giá: {it.unit_price.toLocaleString('vi-VN')}đ
                      </p>
                      {it.note && (
                        <p className="text-[11px] text-emerald-700 mt-0.5 italic">Ghi chú: {it.note}</p>
                      )}
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <span className="font-semibold text-slate-800">
                      {it.total_price.toLocaleString('vi-VN')}đ
                    </span>
                    <span className="block text-[11px] text-slate-400">x{it.quantity}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Financial Summary */}
            <div className="p-4 bg-slate-50 border-t border-slate-200 text-xs space-y-1.5">
              <div className="flex justify-between text-slate-600">
                <span>Tạm tính hàng:</span>
                <span>{order.subtotal.toLocaleString('vi-VN')}đ</span>
              </div>
              {order.discount_amount > 0 && (
                <div className="flex justify-between text-emerald-700 font-medium">
                  <span>Giảm giá khuyến mãi {order.applied_promo_code ? `(${order.applied_promo_code})` : ''}:</span>
                  <span>-{order.discount_amount.toLocaleString('vi-VN')}đ</span>
                </div>
              )}
              <div className="flex justify-between text-slate-600">
                <span>Phí giao hàng:</span>
                <span>{order.shipping_fee.toLocaleString('vi-VN')}đ</span>
              </div>
              {order.shipping_discount > 0 && (
                <div className="flex justify-between text-emerald-700 font-medium">
                  <span>Ưu đãi phí ship:</span>
                  <span>-{order.shipping_discount.toLocaleString('vi-VN')}đ</span>
                </div>
              )}
              <div className="flex justify-between text-sm font-bold text-slate-900 pt-2 border-t border-slate-200">
                <span>Tổng cộng thực thu:</span>
                <span className="text-emerald-700 text-base">{order.total_amount.toLocaleString('vi-VN')}đ</span>
              </div>
            </div>
          </div>

          {/* 5. Payment Status Manual Override */}
          <div className="p-4 bg-slate-50/60 rounded-xl border border-slate-200/80 space-y-3">
            <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Trạng thái thanh toán
            </h4>
            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-600">Hiện tại:</span>
              <Badge variant={PAYMENT_STATUS_LABELS[order.payment_status]?.variant || 'neutral'}>
                {PAYMENT_STATUS_LABELS[order.payment_status]?.text}
              </Badge>
              <div className="flex gap-2 ml-auto">
                {order.payment_status !== 'PAID' && (
                  <Button
                    size="sm"
                    variant="outline"
                    isLoading={actionLoading}
                    onClick={() => handlePaymentStatusChange('PAID')}
                  >
                    ✓ Đánh dấu Đã thanh toán
                  </Button>
                )}
                {order.payment_status === 'PAID' && (
                  <Button
                    size="sm"
                    variant="outline"
                    isLoading={actionLoading}
                    onClick={() => handlePaymentStatusChange('PENDING')}
                  >
                    ↩ Đổi lại Chưa thanh toán
                  </Button>
                )}
              </div>
            </div>
          </div>

          {/* 6. Internal Notes */}
          <div className="p-4 bg-slate-50/60 rounded-xl border border-slate-200/80 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Ghi chú nội bộ (Chỉ nhân viên thấy)
              </h4>
              <Button
                size="sm"
                variant="primary"
                isLoading={savingNote}
                onClick={handleSaveInternalNote}
              >
                Lưu ghi chú
              </Button>
            </div>
            <textarea
              className="w-full text-xs p-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
              rows={3}
              placeholder="Nhập dặn dò shipper, yêu cầu đặc biệt của khách..."
              value={internalNote}
              onChange={(e) => setInternalNote(e.target.value)}
            />
          </div>

          {/* 7. Status History Audit Timeline */}
          <div className="p-4 bg-slate-50/60 rounded-xl border border-slate-200/80 space-y-3">
            <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Lịch sử chuyển trạng thái (Audit Trail)
            </h4>
            <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
              {order.status_history.map((hist) => (
                <div key={hist.id} className="relative text-xs">
                  <div className="absolute -left-6 top-0.5 w-3 h-3 rounded-full bg-emerald-500 ring-4 ring-white" />
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-800">
                      {hist.old_status ? `${hist.old_status} ➔ ` : 'Khởi tạo: '}
                      <span className="text-emerald-700">{hist.new_status}</span>
                    </span>
                    <span className="text-[11px] text-slate-400">
                      {new Date(hist.created_at).toLocaleString('vi-VN')}
                    </span>
                  </div>
                  {hist.reason && (
                    <p className="text-slate-500 text-[11px] mt-0.5 italic">{hist.reason}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}

      {/* Cancel Order Confirm Dialog */}
      <Dialog
        isOpen={isCancelModalOpen}
        onClose={() => setIsCancelModalOpen(false)}
        title="Xác nhận hủy đơn hàng"
        maxWidth="md"
        footer={
          <>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsCancelModalOpen(false)}
              disabled={actionLoading}
            >
              Bỏ qua
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={handleConfirmCancel}
              isLoading={actionLoading}
            >
              Xác nhận hủy đơn
            </Button>
          </>
        }
      >
        <div className="space-y-3">
          <p className="text-sm text-slate-700">
            Bạn có chắc chắn muốn hủy đơn hàng <strong>#{order?.order_number}</strong>?
          </p>
          <div className="p-2.5 bg-amber-50 rounded-lg border border-amber-200 text-xs text-amber-800">
            ℹ️ Toàn bộ số lượng sản phẩm trong đơn sẽ tự động được hoàn trả vào kho hàng (Phiếu nhập RETURN_IN).
          </div>
          <Input
            label="Lý do hủy đơn"
            value={cancelReason}
            onChange={(e) => setCancelReason(e.target.value)}
            placeholder="VD: Khách gọi đổi ý, giao không liên lạc được..."
          />
        </div>
      </Dialog>
    </Drawer>
  );
};
