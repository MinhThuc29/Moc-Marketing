'use client';

import React, { useState } from 'react';
import { Dialog, Button, Input, Badge } from '@moc-healthy/ui';
import {
  Product,
  CartItemCalculationInput,
  PromotionCalculationInput,
  PromotionCalculationResult,
} from '@moc-healthy/contracts';
import { promotionsApi } from '../../lib/api';

interface PromotionCalculatorModalProps {
  isOpen: boolean;
  onClose: () => void;
  products: Product[];
}

export const PromotionCalculatorModal: React.FC<PromotionCalculatorModalProps> = ({
  isOpen,
  onClose,
  products,
}) => {
  // Cart Items for simulation
  const [cartItems, setCartItems] = useState<
    Array<{
      product_id: string;
      quantity: number;
      unit_price: number;
      name: string;
      category_id?: string | null;
    }>
  >(() => {
    if (products.length > 0) {
      return [
        {
          product_id: products[0].id,
          quantity: 2,
          unit_price: products[0].base_price || 150000,
          name: products[0].name,
          category_id: products[0].category_id,
        },
      ];
    }
    return [];
  });

  const [promoCode, setPromoCode] = useState('CHAOBANMOI');
  const [shippingFee, setShippingFee] = useState('30000');
  const [isNewCustomer, setIsNewCustomer] = useState(true);
  const [isCalculating, setIsCalculating] = useState(false);
  const [result, setResult] = useState<PromotionCalculationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Add an item to test cart
  const handleAddItem = () => {
    if (products.length === 0) return;
    const prod = products[cartItems.length % products.length] || products[0];
    setCartItems((prev) => [
      ...prev,
      {
        product_id: prod.id,
        quantity: 1,
        unit_price: prod.base_price || 100000,
        name: prod.name,
        category_id: prod.category_id,
      },
    ]);
  };

  const handleRemoveItem = (index: number) => {
    setCartItems((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpdateItem = (
    index: number,
    field: 'product_id' | 'quantity' | 'unit_price',
    value: any
  ) => {
    setCartItems((prev) => {
      const copy = [...prev];
      if (field === 'product_id') {
        const prod = products.find((p) => p.id === value);
        copy[index] = {
          ...copy[index],
          product_id: value,
          name: prod ? prod.name : copy[index].name,
          unit_price: prod?.base_price ?? copy[index].unit_price,
          category_id: prod?.category_id,
        };
      } else if (field === 'quantity') {
        copy[index] = { ...copy[index], quantity: Math.max(1, parseInt(value, 10) || 1) };
      } else if (field === 'unit_price') {
        copy[index] = { ...copy[index], unit_price: Math.max(0, parseFloat(value) || 0) };
      }
      return copy;
    });
  };

  const handleCalculate = async () => {
    if (cartItems.length === 0) {
      setError('Vui lòng thêm ít nhất 1 sản phẩm vào giỏ hàng thử nghiệm.');
      return;
    }
    setError(null);
    setIsCalculating(true);
    setResult(null);

    const payload: PromotionCalculationInput = {
      items: cartItems.map((ci) => ({
        product_id: ci.product_id,
        quantity: ci.quantity,
        unit_price: ci.unit_price,
        category_id: ci.category_id,
        name: ci.name,
      })),
      promo_code: promoCode.trim() ? promoCode.trim().toUpperCase() : null,
      shipping_fee: parseFloat(shippingFee) || 0,
      is_new_customer: isNewCustomer,
    };

    try {
      const res = await promotionsApi.calculate(payload);
      setResult(res);
    } catch (err: any) {
      console.error('Calculation error:', err);
      setError(err.data?.detail || err.message || 'Lỗi khi tính toán khuyến mãi');
    } finally {
      setIsCalculating(false);
    }
  };

  const formatVnd = (val: number) => {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val);
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="🧪 Mô Phỏng Công Cụ Tính Giá Khuyến Mãi (Promotion Engine)"
      maxWidth="xl"
      footer={
        <div className="flex justify-between items-center w-full">
          <Button variant="ghost" onClick={onClose}>
            Đóng
          </Button>
          <Button
            variant="primary"
            onClick={handleCalculate}
            isLoading={isCalculating}
            className="flex items-center gap-1.5"
          >
            <span>⚡</span> Tính Toán Ngay
          </Button>
        </div>
      }
    >
      <div className="space-y-5 text-sm max-h-[70vh] overflow-y-auto pr-1">
        <p className="text-xs text-slate-500">
          Công cụ tính toán authoritative tại máy chủ backend — đảm bảo quy tắc không thể bị sửa đổi ở máy khách,
          hỗ trợ kiểm thử tức thì mọi kịch bản giảm giá, flash sale, quà tặng, mã voucher và chặn trần.
        </p>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg">
            {error}
          </div>
        )}

        {/* Giỏ hàng thử nghiệm */}
        <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
              🛒 Giỏ Hàng Giả Lập ({cartItems.length} sản phẩm)
            </span>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleAddItem}
              className="text-xs py-1"
            >
              + Thêm món
            </Button>
          </div>

          {cartItems.length === 0 ? (
            <p className="text-xs text-slate-400 py-3 text-center">Chưa có sản phẩm trong giỏ.</p>
          ) : (
            <div className="space-y-2">
              {cartItems.map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 bg-white p-2.5 rounded-lg border border-slate-200 text-xs"
                >
                  <div className="flex-1">
                    <select
                      value={item.product_id}
                      onChange={(e) => handleUpdateItem(idx, 'product_id', e.target.value)}
                      className="w-full text-xs border border-slate-200 rounded p-1 font-medium text-slate-800"
                    >
                      {products.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name} ({formatVnd(p.base_price)})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="w-16">
                    <label className="text-[10px] text-slate-400 block">Số lượng</label>
                    <input
                      type="number"
                      min="1"
                      value={item.quantity}
                      onChange={(e) => handleUpdateItem(idx, 'quantity', e.target.value)}
                      className="w-full text-xs border border-slate-200 rounded p-1 text-center"
                    />
                  </div>
                  <div className="w-24">
                    <label className="text-[10px] text-slate-400 block">Đơn giá</label>
                    <input
                      type="number"
                      step="1000"
                      value={item.unit_price}
                      onChange={(e) => handleUpdateItem(idx, 'unit_price', e.target.value)}
                      className="w-full text-xs border border-slate-200 rounded p-1 text-right"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRemoveItem(idx)}
                    className="text-slate-400 hover:text-red-500 p-1 text-base leading-none"
                    title="Xóa"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Thiết lập tham số */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-slate-50 p-3.5 rounded-xl border border-slate-200">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Mã Voucher (Nhập thử)
            </label>
            <Input
              value={promoCode}
              onChange={(e) => setPromoCode(e.target.value.toUpperCase())}
              placeholder="VD: CHAOBANMOI"
              className="uppercase font-mono text-xs"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Phí vận chuyển (₫)
            </label>
            <Input
              type="number"
              step="1000"
              value={shippingFee}
              onChange={(e) => setShippingFee(e.target.value)}
              placeholder="VD: 30000"
              className="text-xs"
            />
          </div>

          <div className="flex flex-col justify-end pb-1">
            <label className="flex items-center space-x-2 text-xs text-slate-700 cursor-pointer">
              <input
                type="checkbox"
                checked={isNewCustomer}
                onChange={(e) => setIsNewCustomer(e.target.checked)}
                className="rounded text-emerald-600 focus:ring-emerald-500"
              />
              <span className="font-medium">Khách hàng mới (First order)</span>
            </label>
          </div>
        </div>

        {/* Kết quả tính toán Authoritative */}
        {result && (
          <div className="bg-emerald-50/70 border border-emerald-200 rounded-xl p-4 space-y-4 animate-in fade-in">
            <div className="flex items-center justify-between pb-2 border-b border-emerald-200/60">
              <span className="font-bold text-emerald-900 text-xs uppercase tracking-wider flex items-center gap-1.5">
                <span>📋</span> Kết Quả Tính Toán Từ Backend Engine
              </span>
              {promoCode && (
                <span
                  className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                    result.is_code_valid
                      ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                      : 'bg-rose-100 text-rose-800 border border-rose-300'
                  }`}
                >
                  Mã {promoCode}: {result.is_code_valid ? 'Hợp lệ ✅' : 'Không áp dụng ❌'}
                </span>
              )}
            </div>

            {/* Bảng tổng kết số tiền */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-white p-3 rounded-lg border border-emerald-100">
              <div>
                <span className="text-[11px] text-slate-500 block">Tổng tiền hàng:</span>
                <span className="font-bold text-slate-800 text-sm">{formatVnd(result.subtotal)}</span>
              </div>
              <div>
                <span className="text-[11px] text-slate-500 block">Giảm giá CTKM:</span>
                <span className="font-bold text-emerald-600 text-sm">
                  -{formatVnd(result.discount_amount)}
                </span>
              </div>
              <div>
                <span className="text-[11px] text-slate-500 block">Giảm phí ship:</span>
                <span className="font-bold text-emerald-600 text-sm">
                  -{formatVnd(result.shipping_discount)}
                </span>
              </div>
              <div>
                <span className="text-[11px] text-slate-500 block">Khách cần trả:</span>
                <span className="font-extrabold text-emerald-700 text-base">
                  {formatVnd(result.final_total)}
                </span>
              </div>
            </div>

            {/* Chi tiết khuyến mãi áp dụng */}
            {result.applied_promotions.length > 0 && (
              <div className="space-y-1.5">
                <span className="text-xs font-semibold text-slate-800 block">
                  🎉 Khuyến Mãi Đã Áp Dụng:
                </span>
                <div className="space-y-1.5">
                  {result.applied_promotions.map((p, idx) => (
                    <div
                      key={idx}
                      className="bg-white p-2.5 rounded-lg border border-emerald-200 flex items-center justify-between text-xs"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-800">{p.title}</span>
                          {p.code && (
                            <span className="font-mono bg-slate-100 px-1.5 py-0.5 rounded text-[10px] text-slate-600 font-semibold">
                              {p.code}
                            </span>
                          )}
                        </div>
                        <span className="text-slate-500 text-[11px] block">{p.description}</span>
                      </div>
                      <span className="font-bold text-emerald-700 text-xs">
                        -{formatVnd(p.discount_amount)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Quà tặng kèm (Mua X tặng Y) */}
            {result.free_items.length > 0 && (
              <div className="space-y-1.5">
                <span className="text-xs font-semibold text-purple-900 block">
                  🎁 Quà Tặng Kèm Đơn Hàng:
                </span>
                <div className="space-y-1.5">
                  {result.free_items.map((gift, idx) => (
                    <div
                      key={idx}
                      className="bg-purple-50 p-2.5 rounded-lg border border-purple-200 flex items-center justify-between text-xs"
                    >
                      <div>
                        <span className="font-bold text-purple-900">{gift.product_name}</span>
                        <span className="text-purple-600 text-[11px] block">{gift.reason}</span>
                      </div>
                      <span className="font-bold text-purple-700 text-xs">
                        x{gift.quantity} (Miễn phí)
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Lý do từ chối (nếu có) */}
            {result.rejection_reasons.length > 0 && (
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs space-y-1 text-amber-800">
                <span className="font-semibold block">⚠️ Chú ý / Lý do chưa thỏa mãn:</span>
                <ul className="list-disc pl-4 space-y-0.5 text-[11px]">
                  {result.rejection_reasons.map((r, idx) => (
                    <li key={idx}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </Dialog>
  );
};
