'use client';

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  Button,
  Input,
  Select,
} from '@moc-healthy/ui';
import {
  Product,
  PaymentMethod,
  PaymentStatus,
} from '@moc-healthy/contracts';
import { ordersApi, productsApi } from '../../lib/api';

export interface ManualOrderModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOrderCreated: () => void;
}

interface OrderItemInput {
  product_id: string;
  product_name: string;
  unit_price: number;
  quantity: number;
  note?: string;
}

export const ManualOrderModal: React.FC<ManualOrderModalProps> = ({
  isOpen,
  onClose,
  onOrderCreated,
}) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loadingProducts, setLoadingProducts] = useState(false);

  // Form state
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [customerEmail, setCustomerEmail] = useState('');
  const [deliveryAddress, setDeliveryAddress] = useState('Mua trực tiếp tại cửa hàng Mộc Healthy');
  const [source, setSource] = useState('WALK_IN');
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('COD');
  const [paymentStatus, setPaymentStatus] = useState<PaymentStatus>('PAID');
  const [shippingFee, setShippingFee] = useState<number>(0);
  const [customerNote, setCustomerNote] = useState('');
  const [internalNote, setInternalNote] = useState('');

  // Selected items
  const [items, setItems] = useState<OrderItemInput[]>([]);
  const [selectedProductId, setSelectedProductId] = useState('');
  const [itemQty, setItemQty] = useState(1);
  const [itemNote, setItemNote] = useState('');

  // Submitting
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Load active products on open
  useEffect(() => {
    if (!isOpen) return;
    const fetchProducts = async () => {
      setLoadingProducts(true);
      try {
        const res = await productsApi.list({ status: 'ACTIVE', page_size: 50 });
        setProducts(res.items);
        if (res.items.length > 0) {
          setSelectedProductId(res.items[0].id);
        }
      } catch (err) {
        console.error('Không thể tải sản phẩm:', err);
      } finally {
        setLoadingProducts(false);
      }
    };
    fetchProducts();
  }, [isOpen]);

  const handleAddItem = () => {
    if (!selectedProductId) return;
    const found = products.find((p) => p.id === selectedProductId);
    if (!found) return;

    const existingIndex = items.findIndex((it) => it.product_id === selectedProductId);
    if (existingIndex >= 0) {
      const updated = [...items];
      updated[existingIndex].quantity += Number(itemQty);
      if (itemNote) {
        updated[existingIndex].note = itemNote;
      }
      setItems(updated);
    } else {
      setItems([
        ...items,
        {
          product_id: found.id,
          product_name: found.name,
          unit_price: found.sale_price ?? found.base_price,
          quantity: Number(itemQty),
          note: itemNote || undefined,
        },
      ]);
    }

    setItemQty(1);
    setItemNote('');
  };

  const handleRemoveItem = (index: number) => {
    setItems(items.filter((_, idx) => idx !== index));
  };

  const handleUpdateItemQty = (index: number, newQty: number) => {
    if (newQty <= 0) return;
    const updated = [...items];
    updated[index].quantity = newQty;
    setItems(updated);
  };

  const subtotal = items.reduce((sum, it) => sum + it.unit_price * it.quantity, 0);
  const totalAmount = subtotal + Number(shippingFee || 0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!customerName.trim()) {
      setErrorMessage('Vui lòng nhập họ tên khách hàng');
      return;
    }
    if (!customerPhone.trim()) {
      setErrorMessage('Vui lòng nhập số điện thoại khách hàng');
      return;
    }
    if (items.length === 0) {
      setErrorMessage('Vui lòng thêm ít nhất 1 sản phẩm vào đơn hàng');
      return;
    }

    setIsSubmitting(true);
    try {
      await ordersApi.createManual({
        customer_name: customerName.trim(),
        customer_phone: customerPhone.trim(),
        customer_email: customerEmail.trim() || undefined,
        delivery_address: deliveryAddress.trim(),
        customer_note: customerNote.trim() || undefined,
        internal_note: internalNote.trim() || undefined,
        source,
        payment_method: paymentMethod,
        payment_status: paymentStatus,
        shipping_fee: Number(shippingFee || 0),
        items: items.map((it) => ({
          product_id: it.product_id,
          quantity: it.quantity,
          note: it.note,
        })),
      });

      // Reset
      setItems([]);
      setCustomerName('');
      setCustomerPhone('');
      setCustomerEmail('');
      setCustomerNote('');
      setInternalNote('');
      setDeliveryAddress('Mua trực tiếp tại cửa hàng Mộc Healthy');
      onOrderCreated();
      onClose();
    } catch (err: any) {
      setErrorMessage(err.message || 'Không thể tạo đơn hàng thủ công');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="Tạo đơn hàng thủ công (POS / Hotline)"
      description="Tạo nhanh đơn bán lẻ tại quầy hoặc nhận đặt hàng qua điện thoại / Zalo OA"
      maxWidth="xl"
      footer={
        <>
          <Button variant="outline" size="sm" onClick={onClose} disabled={isSubmitting}>
            Hủy bỏ
          </Button>
          <Button variant="primary" size="sm" onClick={handleSubmit} isLoading={isSubmitting}>
            ✓ Hoàn tất tạo đơn
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-5 text-xs text-slate-700 max-h-[75vh] overflow-y-auto pr-1">
        {errorMessage && (
          <div className="p-3 bg-red-50 text-red-700 rounded-lg border border-red-200">
            {errorMessage}
          </div>
        )}

        {/* 1. Thông tin khách hàng */}
        <div className="p-4 bg-slate-50/70 rounded-xl border border-slate-200/80 space-y-3">
          <h4 className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
            1. Thông tin khách hàng & kênh tiếp nhận
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Input
              label="Họ tên khách hàng *"
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
              placeholder="VD: Anh Minh, Chị Lan..."
              required
            />
            <Input
              label="Số điện thoại *"
              value={customerPhone}
              onChange={(e) => setCustomerPhone(e.target.value)}
              placeholder="VD: 0901234567"
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Select
              label="Nguồn đơn hàng"
              value={source}
              onChange={(e) => {
                setSource(e.target.value);
                if (e.target.value === 'WALK_IN') {
                  setDeliveryAddress('Mua trực tiếp tại cửa hàng Mộc Healthy');
                  setPaymentStatus('PAID');
                  setShippingFee(0);
                } else {
                  setPaymentStatus('PENDING');
                }
              }}
              options={[
                { value: 'WALK_IN', label: '🏪 Mua tại quầy (Walk-in)' },
                { value: 'PHONE', label: '📞 Hotline / Điện thoại' },
                { value: 'ZALO', label: '💬 Zalo OA' },
                { value: 'FACEBOOK', label: '🌐 Facebook Messenger' },
              ]}
            />
            <Input
              label="Email (tùy chọn)"
              value={customerEmail}
              onChange={(e) => setCustomerEmail(e.target.value)}
              placeholder="VD: email@example.com"
            />
          </div>

          <Input
            label="Địa chỉ giao hàng *"
            value={deliveryAddress}
            onChange={(e) => setDeliveryAddress(e.target.value)}
            placeholder="Địa chỉ nhận hàng đầy đủ hoặc Mua tại quầy"
            required
          />
        </div>

        {/* 2. Thêm món vào đơn */}
        <div className="p-4 bg-slate-50/70 rounded-xl border border-slate-200/80 space-y-3">
          <h4 className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
            2. Thêm sản phẩm vào đơn ({items.length} món)
          </h4>

          {loadingProducts ? (
            <p className="text-slate-400">Đang tải danh sách sản phẩm...</p>
          ) : (
            <div className="space-y-2">
              <div className="grid grid-cols-1 md:grid-cols-12 gap-2 items-end">
                <div className="md:col-span-6">
                  <Select
                    label="Chọn sản phẩm"
                    value={selectedProductId}
                    onChange={(e) => setSelectedProductId(e.target.value)}
                    options={products.map((p) => ({
                      value: p.id,
                      label: `${p.name} (${(p.sale_price ?? p.base_price).toLocaleString('vi-VN')}đ / ${p.unit})`,
                    }))}
                  />
                </div>
                <div className="md:col-span-2">
                  <Input
                    label="Số lượng"
                    type="number"
                    min="1"
                    value={itemQty}
                    onChange={(e) => setItemQty(Math.max(1, parseInt(e.target.value) || 1))}
                  />
                </div>
                <div className="md:col-span-3">
                  <Input
                    label="Ghi chú món"
                    value={itemNote}
                    onChange={(e) => setItemNote(e.target.value)}
                    placeholder="VD: Ít ngọt, gọt sẵn"
                  />
                </div>
                <div className="md:col-span-1">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="w-full h-9 flex items-center justify-center font-bold"
                    onClick={handleAddItem}
                  >
                    +
                  </Button>
                </div>
              </div>

              {/* Items List */}
              {items.length > 0 && (
                <div className="mt-3 border border-slate-200 rounded-lg overflow-hidden bg-white divide-y divide-slate-100">
                  {items.map((it, idx) => (
                    <div key={idx} className="p-3 flex items-center justify-between gap-2">
                      <div className="flex-1">
                        <p className="font-semibold text-slate-800">{it.product_name}</p>
                        <p className="text-[11px] text-slate-400">
                          {it.unit_price.toLocaleString('vi-VN')}đ x {it.quantity} = {(it.unit_price * it.quantity).toLocaleString('vi-VN')}đ
                          {it.note ? ` | Note: ${it.note}` : ''}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <input
                          type="number"
                          min="1"
                          value={it.quantity}
                          onChange={(e) => handleUpdateItemQty(idx, parseInt(e.target.value) || 1)}
                          className="w-14 px-2 py-1 text-xs border border-slate-200 rounded text-center"
                        />
                        <button
                          type="button"
                          onClick={() => handleRemoveItem(idx)}
                          className="text-red-500 hover:text-red-700 p-1 text-xs"
                          title="Xóa món"
                        >
                          ✕
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* 3. Thanh toán & Giao nhận */}
        <div className="p-4 bg-slate-50/70 rounded-xl border border-slate-200/80 space-y-3">
          <h4 className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
            3. Phương thức thanh toán & Chi phí
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <Select
              label="Phương thức thanh toán"
              value={paymentMethod}
              onChange={(e) => setPaymentMethod(e.target.value as PaymentMethod)}
              options={[
                { value: 'COD', label: '💵 Tiền mặt (COD)' },
                { value: 'BANK_TRANSFER', label: '📲 Chuyển khoản VietQR' },
              ]}
            />
            <Select
              label="Trạng thái thanh toán"
              value={paymentStatus}
              onChange={(e) => setPaymentStatus(e.target.value as PaymentStatus)}
              options={[
                { value: 'PAID', label: '✓ Đã thanh toán (Thu tiền ngay)' },
                { value: 'PENDING', label: '⏳ Chờ thanh toán' },
              ]}
            />
            <Input
              label="Phí giao hàng (VND)"
              type="number"
              min="0"
              step="1000"
              value={shippingFee}
              onChange={(e) => setShippingFee(Math.max(0, parseInt(e.target.value) || 0))}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Input
              label="Ghi chú của khách"
              value={customerNote}
              onChange={(e) => setCustomerNote(e.target.value)}
              placeholder="VD: Không lấy đá, dặn bảo vệ nhận giúp..."
            />
            <Input
              label="Ghi chú nội bộ thu ngân/quản trị"
              value={internalNote}
              onChange={(e) => setInternalNote(e.target.value)}
              placeholder="VD: Khách thân thiết, tặng kèm thìa gỗ..."
            />
          </div>

          {/* Totals Preview */}
          <div className="p-3 bg-white rounded-lg border border-slate-200 space-y-1 text-right">
            <div className="text-slate-500">
              Tạm tính ({items.length} món): <strong>{subtotal.toLocaleString('vi-VN')}đ</strong>
            </div>
            <div className="text-slate-500">
              Phí ship: <strong>{shippingFee.toLocaleString('vi-VN')}đ</strong>
            </div>
            <div className="text-sm font-bold text-emerald-800 pt-1 border-t border-slate-100">
              Tổng thanh toán: <span className="text-base text-emerald-700">{totalAmount.toLocaleString('vi-VN')}đ</span>
            </div>
          </div>
        </div>
      </form>
    </Dialog>
  );
};
