'use client';

import React, { useState, useEffect } from 'react';
import { Drawer, Button, Input, Select, Badge } from '@moc-healthy/ui';
import {
  Promotion,
  PromotionCreateInput,
  PromotionType,
  PromotionStatus,
  ProductScope,
  CustomerScope,
  Product,
  Category,
} from '@moc-healthy/contracts';
import { promotionsApi } from '../../lib/api';

interface PromotionFormDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  promotionToEdit?: Promotion | null;
  products: Product[];
  categories: Category[];
}

function formatDateForInput(dateStr?: string): string {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return '';
  const pad = (n: number) => String(n).padStart(2, '0');
  const yyyy = d.getFullYear();
  const MM = pad(d.getMonth() + 1);
  const dd = pad(d.getDate());
  const hh = pad(d.getHours());
  const mm = pad(d.getMinutes());
  return `${yyyy}-${MM}-${dd}T${hh}:${mm}`;
}

function getDefaultDates() {
  const now = new Date();
  const nextWeek = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
  return {
    start_at: formatDateForInput(now.toISOString()),
    end_at: formatDateForInput(nextWeek.toISOString()),
  };
}

export const PromotionFormDrawer: React.FC<PromotionFormDrawerProps> = ({
  isOpen,
  onClose,
  onSuccess,
  promotionToEdit,
  products,
  categories,
}) => {
  const isEditing = Boolean(promotionToEdit);
  const defaults = getDefaultDates();

  const [formData, setFormData] = useState({
    title: '',
    code: '',
    description: '',
    type: 'PERCENT_DISCOUNT' as PromotionType,
    value: '10',
    min_order_value: '',
    max_discount: '',
    start_at: defaults.start_at,
    end_at: defaults.end_at,
    product_scope: 'ALL' as ProductScope,
    applicable_product_ids: [] as string[],
    applicable_category_ids: [] as string[],
    customer_scope: 'ALL' as CustomerScope,
    usage_limit: '',
    usage_per_customer: '1',
    stackable: false,
    status: 'ACTIVE' as PromotionStatus,

    // Buy X Get Y details
    buy_product_id: '',
    buy_quantity: '2',
    get_product_id: '',
    get_quantity: '1',
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (promotionToEdit) {
      const buyConfig = promotionToEdit.buy_x_get_y_config || {};
      setFormData({
        title: promotionToEdit.title || '',
        code: promotionToEdit.code || '',
        description: promotionToEdit.description || '',
        type: promotionToEdit.type || 'PERCENT_DISCOUNT',
        value: String(promotionToEdit.value || 0),
        min_order_value: promotionToEdit.min_order_value ? String(promotionToEdit.min_order_value) : '',
        max_discount: promotionToEdit.max_discount ? String(promotionToEdit.max_discount) : '',
        start_at: formatDateForInput(promotionToEdit.start_at),
        end_at: formatDateForInput(promotionToEdit.end_at),
        product_scope: promotionToEdit.product_scope || 'ALL',
        applicable_product_ids: promotionToEdit.applicable_product_ids || [],
        applicable_category_ids: promotionToEdit.applicable_category_ids || [],
        customer_scope: promotionToEdit.customer_scope || 'ALL',
        usage_limit: promotionToEdit.usage_limit ? String(promotionToEdit.usage_limit) : '',
        usage_per_customer: String(promotionToEdit.usage_per_customer ?? 1),
        stackable: Boolean(promotionToEdit.stackable),
        status: promotionToEdit.status || 'ACTIVE',

        buy_product_id: buyConfig.buy_product_id || '',
        buy_quantity: String(buyConfig.buy_quantity || 2),
        get_product_id: buyConfig.get_product_id || '',
        get_quantity: String(buyConfig.get_quantity || 1),
      });
    } else {
      const freshDates = getDefaultDates();
      setFormData({
        title: '',
        code: '',
        description: '',
        type: 'PERCENT_DISCOUNT',
        value: '10',
        min_order_value: '',
        max_discount: '',
        start_at: freshDates.start_at,
        end_at: freshDates.end_at,
        product_scope: 'ALL',
        applicable_product_ids: [],
        applicable_category_ids: [],
        customer_scope: 'ALL',
        usage_limit: '',
        usage_per_customer: '1',
        stackable: false,
        status: 'ACTIVE',

        buy_product_id: products[0]?.id || '',
        buy_quantity: '2',
        get_product_id: products[0]?.id || '',
        get_quantity: '1',
      });
    }
    setErrorMessage(null);
  }, [promotionToEdit, isOpen, products]);

  const generateRandomCode = () => {
    const prefixes = ['HEALTHY', 'MOC', 'SALE', 'DEAL', 'VIP', 'FREESHIP'];
    const p = prefixes[Math.floor(Math.random() * prefixes.length)];
    const num = Math.floor(10 + Math.random() * 90);
    setFormData((prev) => ({ ...prev, code: `${p}${num}` }));
  };

  const handleProductToggle = (prodId: string) => {
    setFormData((prev) => {
      const exists = prev.applicable_product_ids.includes(prodId);
      return {
        ...prev,
        applicable_product_ids: exists
          ? prev.applicable_product_ids.filter((id) => id !== prodId)
          : [...prev.applicable_product_ids, prodId],
      };
    });
  };

  const handleCategoryToggle = (catId: string) => {
    setFormData((prev) => {
      const exists = prev.applicable_category_ids.includes(catId);
      return {
        ...prev,
        applicable_category_ids: exists
          ? prev.applicable_category_ids.filter((id) => id !== catId)
          : [...prev.applicable_category_ids, catId],
      };
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!formData.title.trim()) {
      setErrorMessage('Vui lòng nhập tên chương trình khuyến mãi');
      return;
    }

    const valNum = parseFloat(formData.value);
    if (isNaN(valNum) || valNum <= 0) {
      setErrorMessage('Giá trị ưu đãi phải là số lớn hơn 0');
      return;
    }

    if (
      (formData.type === 'PERCENT_DISCOUNT' || formData.type === 'FLASH_SALE') &&
      valNum > 100
    ) {
      setErrorMessage('Tỷ lệ giảm phần trăm không được vượt quá 100%');
      return;
    }

    if (!formData.start_at || !formData.end_at) {
      setErrorMessage('Vui lòng chọn thời gian bắt đầu và kết thúc');
      return;
    }

    const startDate = new Date(formData.start_at);
    const endDate = new Date(formData.end_at);
    if (endDate <= startDate) {
      setErrorMessage('Thời gian kết thúc phải lớn hơn thời gian bắt đầu');
      return;
    }

    let buyConfig: Record<string, any> | null = null;
    if (formData.type === 'BUY_X_GET_Y') {
      if (!formData.buy_product_id || !formData.get_product_id) {
        setErrorMessage('Vui lòng chọn sản phẩm Mua và sản phẩm Tặng cho Mua X Tặng Y');
        return;
      }
      buyConfig = {
        buy_product_id: formData.buy_product_id,
        buy_quantity: parseInt(formData.buy_quantity, 10) || 1,
        get_product_id: formData.get_product_id,
        get_quantity: parseInt(formData.get_quantity, 10) || 1,
      };
    }

    const payload: PromotionCreateInput = {
      title: formData.title.trim(),
      code: formData.code.trim() ? formData.code.trim().toUpperCase() : null,
      description: formData.description.trim() || null,
      type: formData.type,
      value: valNum,
      min_order_value: formData.min_order_value ? parseFloat(formData.min_order_value) : null,
      max_discount: formData.max_discount ? parseFloat(formData.max_discount) : null,
      start_at: startDate.toISOString(),
      end_at: endDate.toISOString(),
      product_scope: formData.product_scope,
      applicable_product_ids:
        formData.product_scope === 'SPECIFIC_PRODUCTS' ? formData.applicable_product_ids : [],
      applicable_category_ids:
        formData.product_scope === 'SPECIFIC_CATEGORIES' ? formData.applicable_category_ids : [],
      buy_x_get_y_config: buyConfig,
      customer_scope: formData.customer_scope,
      usage_limit: formData.usage_limit ? parseInt(formData.usage_limit, 10) : null,
      usage_per_customer: formData.usage_per_customer ? parseInt(formData.usage_per_customer, 10) : 1,
      stackable: formData.stackable,
      status: formData.status,
    };

    setIsSubmitting(true);
    try {
      if (isEditing && promotionToEdit) {
        await promotionsApi.update(promotionToEdit.id, payload);
      } else {
        await promotionsApi.create(payload);
      }
      onSuccess();
      onClose();
    } catch (err: any) {
      console.error('Save promotion error:', err);
      setErrorMessage(err.data?.detail || err.message || 'Lưu chương trình thất bại');
    } finally {
      setIsSubmitting(false);
    }
  };

  const isPercentType =
    formData.type === 'PERCENT_DISCOUNT' ||
    formData.type === 'FLASH_SALE' ||
    formData.type === 'FREE_SHIPPING';

  return (
    <Drawer
      isOpen={isOpen}
      onClose={onClose}
      title={isEditing ? 'Chỉnh Sửa Khuyến Mãi' : 'Tạo Chương Trình Khuyến Mãi Mới'}
      maxWidth="xl"
      footer={
        <div className="flex items-center justify-between w-full">
          <Button variant="ghost" type="button" onClick={onClose} disabled={isSubmitting}>
            Hủy
          </Button>
          <Button variant="primary" type="button" onClick={handleSubmit} isLoading={isSubmitting}>
            {isEditing ? 'Cập Nhật' : 'Lưu & Kích Hoạt'}
          </Button>
        </div>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-6 pb-6 text-sm">
        {errorMessage && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-xs">
            {errorMessage}
          </div>
        )}

        {/* Thông tin cơ bản */}
        <div className="bg-slate-50 p-4 rounded-xl space-y-4 border border-slate-200/80">
          <h4 className="font-semibold text-slate-800 text-xs uppercase tracking-wider flex items-center gap-1.5">
            <span>🏷️</span> Thông Tin Chương Trình
          </h4>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Tên chương trình <span className="text-red-500">*</span>
            </label>
            <Input
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="VD: Flash Sale Giảm 15% Toàn Sàn, Mua 2 Hạt Điều Tặng 1 Granola..."
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Mã Voucher (Tùy chọn)
              </label>
              <div className="flex gap-2">
                <Input
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                  placeholder="VD: MOC10, FREESHIP"
                  className="uppercase font-mono font-semibold"
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={generateRandomCode}
                  className="shrink-0 text-xs"
                  title="Tạo mã tự động"
                >
                  🎲 Tự tạo
                </Button>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">Để trống nếu muốn áp dụng tự động toàn sàn.</p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Trạng thái hoạt động
              </label>
              <Select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value as PromotionStatus })}
                options={[
                  { value: 'ACTIVE', label: '🟢 Đang chạy (Active)' },
                  { value: 'PAUSED', label: '⏸️ Tạm dừng (Paused)' },
                  { value: 'DRAFT', label: '📝 Bản nháp (Draft)' },
                ]}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Mô tả chi tiết / Thể lệ chương trình
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={2}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 bg-white"
              placeholder="VD: Áp dụng cho mọi khách hàng mua từ 2 sản phẩm trở lên. Không áp dụng đồng thời với voucher khác."
            />
          </div>
        </div>

        {/* Loại & Giá trị ưu đãi */}
        <div className="bg-slate-50 p-4 rounded-xl space-y-4 border border-slate-200/80">
          <h4 className="font-semibold text-slate-800 text-xs uppercase tracking-wider flex items-center gap-1.5">
            <span>💰</span> Loại Khuyến Mãi & Mức Giảm
          </h4>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Loại hình khuyến mãi <span className="text-red-500">*</span>
              </label>
              <Select
                value={formData.type}
                onChange={(e) => setFormData({ ...formData, type: e.target.value as PromotionType })}
                options={[
                  { value: 'PERCENT_DISCOUNT', label: 'Giảm theo phần trăm (%)' },
                  { value: 'FIXED_DISCOUNT', label: 'Giảm số tiền cố định (₫)' },
                  { value: 'FLASH_SALE', label: 'Flash Sale giờ vàng (%)' },
                  { value: 'BUY_X_GET_Y', label: 'Mua X Tặng Y (Quà tặng)' },
                  { value: 'COMBO', label: 'Combo Mộc Healthy (Giảm giá gói)' },
                  { value: 'FREE_SHIPPING', label: 'Miễn phí vận chuyển (Freeship)' },
                  { value: 'VOUCHER', label: 'Mã Voucher cá nhân/chiến dịch (₫)' },
                ]}
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                {isPercentType ? 'Mức giảm (%)' : 'Số tiền giảm (₫)'} <span className="text-red-500">*</span>
              </label>
              <Input
                type="number"
                min="0"
                step="any"
                value={formData.value}
                onChange={(e) => setFormData({ ...formData, value: e.target.value })}
                placeholder={isPercentType ? 'VD: 15 (tương đương 15%)' : 'VD: 50000'}
                required
              />
            </div>
          </div>

          {/* Config Mua X Tang Y */}
          {formData.type === 'BUY_X_GET_Y' && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg space-y-3">
              <span className="text-xs font-semibold text-emerald-800 block">
                🎁 Cấu hình Mua X Tặng Y:
              </span>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-medium text-slate-700 mb-1">Sản phẩm mua</label>
                  <Select
                    value={formData.buy_product_id}
                    onChange={(e) => setFormData({ ...formData, buy_product_id: e.target.value })}
                    options={products.map((p) => ({ value: p.id, label: `${p.name} (${p.sku})` }))}
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-700 mb-1">Số lượng mua (X)</label>
                  <Input
                    type="number"
                    min="1"
                    value={formData.buy_quantity}
                    onChange={(e) => setFormData({ ...formData, buy_quantity: e.target.value })}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-medium text-slate-700 mb-1">Sản phẩm tặng</label>
                  <Select
                    value={formData.get_product_id}
                    onChange={(e) => setFormData({ ...formData, get_product_id: e.target.value })}
                    options={products.map((p) => ({ value: p.id, label: `${p.name} (${p.sku})` }))}
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-700 mb-1">Số lượng tặng (Y)</label>
                  <Input
                    type="number"
                    min="1"
                    value={formData.get_quantity}
                    onChange={(e) => setFormData({ ...formData, get_quantity: e.target.value })}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Điều kiện chặn trần */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Giá trị đơn hàng tối thiểu (₫)
              </label>
              <Input
                type="number"
                min="0"
                step="1000"
                value={formData.min_order_value}
                onChange={(e) => setFormData({ ...formData, min_order_value: e.target.value })}
                placeholder="VD: 200000 (Để trống nếu không yêu cầu)"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Mức giảm tối đa (₫) (Chặn trần cho %)
              </label>
              <Input
                type="number"
                min="0"
                step="1000"
                value={formData.max_discount}
                onChange={(e) => setFormData({ ...formData, max_discount: e.target.value })}
                placeholder="VD: 50000 (Chặn mức giảm tối đa)"
              />
            </div>
          </div>
        </div>

        {/* Thời gian hiệu lực */}
        <div className="bg-slate-50 p-4 rounded-xl space-y-4 border border-slate-200/80">
          <h4 className="font-semibold text-slate-800 text-xs uppercase tracking-wider flex items-center gap-1.5">
            <span>⏰</span> Thời Gian Hiệu Lực
          </h4>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Thời gian bắt đầu <span className="text-red-500">*</span>
              </label>
              <Input
                type="datetime-local"
                value={formData.start_at}
                onChange={(e) => setFormData({ ...formData, start_at: e.target.value })}
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Thời gian kết thúc <span className="text-red-500">*</span>
              </label>
              <Input
                type="datetime-local"
                value={formData.end_at}
                onChange={(e) => setFormData({ ...formData, end_at: e.target.value })}
                required
              />
            </div>
          </div>
        </div>

        {/* Phạm vi áp dụng */}
        <div className="bg-slate-50 p-4 rounded-xl space-y-4 border border-slate-200/80">
          <h4 className="font-semibold text-slate-800 text-xs uppercase tracking-wider flex items-center gap-1.5">
            <span>🎯</span> Phạm Vi Áp Dụng
          </h4>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Phạm vi sản phẩm
              </label>
              <Select
                value={formData.product_scope}
                onChange={(e) => setFormData({ ...formData, product_scope: e.target.value as ProductScope })}
                options={[
                  { value: 'ALL', label: 'Toàn bộ sản phẩm' },
                  { value: 'SPECIFIC_PRODUCTS', label: 'Chỉ sản phẩm được chọn' },
                  { value: 'SPECIFIC_CATEGORIES', label: 'Theo danh mục ngành hàng' },
                ]}
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Đối tượng khách hàng
              </label>
              <Select
                value={formData.customer_scope}
                onChange={(e) => setFormData({ ...formData, customer_scope: e.target.value as CustomerScope })}
                options={[
                  { value: 'ALL', label: 'Tất cả khách hàng' },
                  { value: 'NEW_CUSTOMER', label: 'Chỉ khách hàng mới' },
                  { value: 'VIP', label: 'Khách hàng VIP' },
                ]}
              />
            </div>
          </div>

          {/* Chọn danh mục */}
          {formData.product_scope === 'SPECIFIC_CATEGORIES' && (
            <div className="p-3 bg-white border border-slate-200 rounded-lg space-y-2">
              <span className="text-xs font-medium text-slate-700 block">
                Chọn các danh mục áp dụng:
              </span>
              <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto">
                {categories.map((cat) => (
                  <label
                    key={cat.id}
                    className="flex items-center space-x-2 text-xs text-slate-700 cursor-pointer hover:bg-slate-50 p-1.5 rounded"
                  >
                    <input
                      type="checkbox"
                      checked={formData.applicable_category_ids.includes(cat.id)}
                      onChange={() => handleCategoryToggle(cat.id)}
                      className="rounded text-emerald-600 focus:ring-emerald-500"
                    />
                    <span>{cat.name}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Chọn sản phẩm */}
          {formData.product_scope === 'SPECIFIC_PRODUCTS' && (
            <div className="p-3 bg-white border border-slate-200 rounded-lg space-y-2">
              <span className="text-xs font-medium text-slate-700 block">
                Chọn các sản phẩm áp dụng: ({formData.applicable_product_ids.length} đã chọn)
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-48 overflow-y-auto">
                {products.map((p) => (
                  <label
                    key={p.id}
                    className="flex items-center space-x-2 text-xs text-slate-700 cursor-pointer hover:bg-slate-50 p-1.5 rounded border border-slate-100"
                  >
                    <input
                      type="checkbox"
                      checked={formData.applicable_product_ids.includes(p.id)}
                      onChange={() => handleProductToggle(p.id)}
                      className="rounded text-emerald-600 focus:ring-emerald-500"
                    />
                    <span className="truncate">{p.name}</span>
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Giới hạn sử dụng & Gộp khuyến mãi */}
        <div className="bg-slate-50 p-4 rounded-xl space-y-4 border border-slate-200/80">
          <h4 className="font-semibold text-slate-800 text-xs uppercase tracking-wider flex items-center gap-1.5">
            <span>🛡️</span> Giới Hạn Sử Dụng & Quy Tắc Gộp
          </h4>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Tổng lượt dùng toàn hệ thống
              </label>
              <Input
                type="number"
                min="1"
                value={formData.usage_limit}
                onChange={(e) => setFormData({ ...formData, usage_limit: e.target.value })}
                placeholder="VD: 500 (Để trống nếu không giới hạn)"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Lượt dùng tối đa / khách hàng
              </label>
              <Input
                type="number"
                min="1"
                value={formData.usage_per_customer}
                onChange={(e) => setFormData({ ...formData, usage_per_customer: e.target.value })}
                placeholder="VD: 1"
              />
            </div>
          </div>

          <div className="flex items-start space-x-2.5 pt-1">
            <input
              type="checkbox"
              id="stackable-toggle"
              checked={formData.stackable}
              onChange={(e) => setFormData({ ...formData, stackable: e.target.checked })}
              className="mt-0.5 rounded text-emerald-600 focus:ring-emerald-500"
            />
            <label htmlFor="stackable-toggle" className="text-xs text-slate-700 cursor-pointer leading-relaxed">
              <span className="font-medium text-slate-800">Cho phép cộng dồn (Stackable)</span>
              <span className="block text-[11px] text-slate-500">
                Mặc định tắt. Khi bật, khách hàng có thể áp dụng thêm cùng với các chương trình khuyến mãi khác.
              </span>
            </label>
          </div>
        </div>
      </form>
    </Drawer>
  );
};
