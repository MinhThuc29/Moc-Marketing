'use client';

import React, { useState, useEffect } from 'react';
import { Drawer, Button, Input, Select, Badge } from '@moc-healthy/ui';
import { Product, Category, ProductStatus } from '@moc-healthy/contracts';
import { productsApi } from '../../lib/api';
import { MediaLibraryModal } from '../media/MediaLibraryModal';

interface ProductFormDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  productToEdit?: Product | null;
  categories: Category[];
}

export const ProductFormDrawer: React.FC<ProductFormDrawerProps> = ({
  isOpen,
  onClose,
  onSuccess,
  productToEdit,
  categories,
}) => {
  const isEditing = Boolean(productToEdit);

  const [formData, setFormData] = useState({
    name: '',
    sku: '',
    slug: '',
    category_id: '',
    base_price: '',
    sale_price: '',
    cost_price: '',
    unit: 'phần',
    status: 'ACTIVE' as ProductStatus,
    featured: false,
    tags: '',
    ingredients: '',
    allergens: '',
    nutrition_text: '',
    shelf_life: '',
    storage_note: '',
    preparation_note: '',
    thumbnail: '',
    seo_title: '',
    seo_description: '',
    change_reason: '',
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isMediaModalOpen, setIsMediaModalOpen] = useState(false);

  // Sync state when drawer opens or editing target changes
  useEffect(() => {
    if (productToEdit) {
      setFormData({
        name: productToEdit.name || '',
        sku: productToEdit.sku || '',
        slug: productToEdit.slug || '',
        category_id: productToEdit.category_id || '',
        base_price: String(productToEdit.base_price || ''),
        sale_price: productToEdit.sale_price !== null && productToEdit.sale_price !== undefined ? String(productToEdit.sale_price) : '',
        cost_price: productToEdit.cost_price !== null && productToEdit.cost_price !== undefined ? String(productToEdit.cost_price) : '',
        unit: productToEdit.unit || 'phần',
        status: productToEdit.status || 'ACTIVE',
        featured: Boolean(productToEdit.featured),
        tags: Array.isArray(productToEdit.tags) ? productToEdit.tags.join(', ') : '',
        ingredients: productToEdit.ingredients || '',
        allergens: productToEdit.allergens || '',
        nutrition_text: productToEdit.nutrition_text || '',
        shelf_life: productToEdit.shelf_life || '',
        storage_note: productToEdit.storage_note || '',
        preparation_note: productToEdit.preparation_note || '',
        thumbnail: productToEdit.thumbnail || '',
        seo_title: productToEdit.seo_title || '',
        seo_description: productToEdit.seo_description || '',
        change_reason: '',
      });
    } else {
      setFormData({
        name: '',
        sku: '',
        slug: '',
        category_id: categories.length > 0 ? categories[0].id : '',
        base_price: '',
        sale_price: '',
        cost_price: '',
        unit: 'hộp',
        status: 'ACTIVE',
        featured: false,
        tags: 'fresh, healthy',
        ingredients: '',
        allergens: '',
        nutrition_text: '',
        shelf_life: '2 ngày',
        storage_note: 'Bảo quản ngăn mát 2-6°C',
        preparation_note: '',
        thumbnail: '',
        seo_title: '',
        seo_description: '',
        change_reason: '',
      });
    }
    setErrorMessage(null);
  }, [productToEdit, isOpen, categories]);

  // Real-time price validation
  const basePriceNum = parseFloat(formData.base_price) || 0;
  const salePriceNum = formData.sale_price ? parseFloat(formData.sale_price) : null;
  const isSalePriceInvalid = salePriceNum !== null && salePriceNum > basePriceNum;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!formData.name.trim()) {
      setErrorMessage('Vui lòng nhập tên sản phẩm');
      return;
    }
    if (!formData.sku.trim()) {
      setErrorMessage('Vui lòng nhập mã SKU định danh');
      return;
    }
    if (isNaN(basePriceNum) || basePriceNum < 0) {
      setErrorMessage('Giá gốc phải là số dương hợp lệ');
      return;
    }
    if (isSalePriceInvalid) {
      setErrorMessage('Giá khuyến mãi không được lớn hơn giá gốc niêm yết!');
      return;
    }

    setIsSubmitting(true);
    try {
      const payload: any = {
        name: formData.name.trim(),
        sku: formData.sku.trim().toUpperCase(),
        slug: formData.slug.trim() || undefined,
        category_id: formData.category_id || undefined,
        base_price: basePriceNum,
        sale_price: salePriceNum,
        cost_price: formData.cost_price ? parseFloat(formData.cost_price) : undefined,
        unit: formData.unit.trim(),
        status: formData.status,
        featured: formData.featured,
        tags: formData.tags
          ? formData.tags.split(',').map((t) => t.trim()).filter(Boolean)
          : [],
        ingredients: formData.ingredients.trim() || undefined,
        allergens: formData.allergens.trim() || undefined,
        nutrition_text: formData.nutrition_text.trim() || undefined,
        shelf_life: formData.shelf_life.trim() || undefined,
        storage_note: formData.storage_note.trim() || undefined,
        preparation_note: formData.preparation_note.trim() || undefined,
        thumbnail: formData.thumbnail.trim() || undefined,
        seo_title: formData.seo_title.trim() || undefined,
        seo_description: formData.seo_description.trim() || undefined,
      };

      if (isEditing && productToEdit) {
        if (formData.change_reason.trim()) {
          payload.change_reason = formData.change_reason.trim();
        }
        await productsApi.update(productToEdit.id, payload);
      } else {
        await productsApi.create(payload);
      }

      onSuccess();
      onClose();
    } catch (err: any) {
      setErrorMessage(err.message || 'Lỗi khi lưu sản phẩm. Vui lòng kiểm tra lại thông tin.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const statusOptions = [
    { label: 'Đang bán (ACTIVE)', value: 'ACTIVE' },
    { label: 'Hết hàng (OUT_OF_STOCK)', value: 'OUT_OF_STOCK' },
    { label: 'Bản nháp (DRAFT)', value: 'DRAFT' },
    { label: 'Ẩn (HIDDEN)', value: 'HIDDEN' },
    { label: 'Lưu trữ (ARCHIVED)', value: 'ARCHIVED' },
  ];

  const categoryOptions = [
    { label: '-- Chưa phân danh mục --', value: '' },
    ...categories.map((c) => ({ label: c.name, value: c.id })),
  ];

  return (
    <Drawer
      isOpen={isOpen}
      onClose={onClose}
      title={isEditing ? `Chỉnh sửa: ${productToEdit?.name}` : 'Thêm sản phẩm F&B mới'}
      maxWidth="xl"
      footer={
        <div className="flex justify-between items-center w-full">
          <Button variant="ghost" type="button" onClick={onClose} disabled={isSubmitting}>
            Hủy bỏ
          </Button>
          <div className="flex gap-2">
            <Button
              variant="primary"
              type="submit"
              form="product-form"
              isLoading={isSubmitting}
              disabled={isSalePriceInvalid}
            >
              {isEditing ? 'Lưu thay đổi' : 'Tạo sản phẩm'}
            </Button>
          </div>
        </div>
      }
    >
      <form id="product-form" onSubmit={handleSubmit} className="space-y-6">
        {errorMessage && (
          <div className="p-3.5 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 flex items-start gap-2">
            <span className="text-base font-bold">⚠️</span>
            <div>{errorMessage}</div>
          </div>
        )}

        {/* Section 1: Thông tin cơ bản */}
        <div className="space-y-4">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 border-b border-slate-100 pb-1.5">
            1. Thông tin định danh & Phân loại
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <Input
                label="Tên sản phẩm *"
                placeholder="VD: Táo New Zealand giòn ngọt"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </div>
            <div>
              <Input
                label="Mã SKU *"
                placeholder="VD: FRUIT-TAO-NZ"
                value={formData.sku}
                onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                required
              />
            </div>
            <div>
              <Input
                label="Slug URL (tùy chọn)"
                placeholder="Tự động sinh nếu để trống"
                value={formData.slug}
                onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
              />
            </div>
            <div>
              <Select
                label="Danh mục sản phẩm"
                options={categoryOptions}
                value={formData.category_id}
                onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
              />
            </div>
            <div>
              <Input
                label="Đơn vị tính *"
                placeholder="hộp, ly, chai, phần..."
                value={formData.unit}
                onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                required
              />
            </div>
            <div>
              <Select
                label="Trạng thái kinh doanh"
                options={statusOptions}
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value as ProductStatus })}
              />
            </div>
            <div className="flex items-center pt-6">
              <label className="flex items-center gap-2.5 cursor-pointer text-sm font-medium text-slate-700">
                <input
                  type="checkbox"
                  checked={formData.featured}
                  onChange={(e) => setFormData({ ...formData, featured: e.target.checked })}
                  className="w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500"
                />
                <span>⭐ Sản phẩm nổi bật (Best Seller / Featured)</span>
              </label>
            </div>
          </div>
        </div>

        {/* Section 2: Định giá & Quy tắc kinh doanh */}
        <div className="space-y-4">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 border-b border-slate-100 pb-1.5">
            2. Bảng giá & Quy tắc doanh thu (VND)
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Input
                label="Giá niêm yết (Base Price) *"
                type="number"
                min="0"
                step="1000"
                placeholder="49000"
                value={formData.base_price}
                onChange={(e) => setFormData({ ...formData, base_price: e.target.value })}
                required
              />
            </div>
            <div>
              <Input
                label="Giá khuyến mãi (Sale Price)"
                type="number"
                min="0"
                step="1000"
                placeholder="Để trống nếu không giảm"
                value={formData.sale_price}
                onChange={(e) => setFormData({ ...formData, sale_price: e.target.value })}
                error={isSalePriceInvalid ? 'Sale price không được lớn hơn base price' : undefined}
              />
            </div>
            <div>
              <Input
                label="Giá vốn ước tính (Cost Price)"
                type="number"
                min="0"
                step="1000"
                placeholder="25000"
                value={formData.cost_price}
                onChange={(e) => setFormData({ ...formData, cost_price: e.target.value })}
              />
            </div>
          </div>

          {/* Pricing indicator */}
          {basePriceNum > 0 && salePriceNum !== null && !isSalePriceInvalid && (
            <div className="p-2.5 bg-emerald-50 border border-emerald-100 rounded-lg text-xs text-emerald-800 flex items-center justify-between">
              <span>
                Giảm giá:{' '}
                <strong className="font-semibold">
                  {Math.round(((basePriceNum - salePriceNum) / basePriceNum) * 100)}%
                </strong>{' '}
                (Tiết kiệm {(basePriceNum - salePriceNum).toLocaleString('vi-VN')} đ)
              </span>
              <Badge variant="success">Hợp lệ</Badge>
            </div>
          )}

          {isEditing && (
            <div>
              <Input
                label="Lý do điều chỉnh giá (Audit Log)"
                placeholder="VD: Thay đổi theo mùa vụ / Chi phí nguyên liệu biến động"
                value={formData.change_reason}
                onChange={(e) => setFormData({ ...formData, change_reason: e.target.value })}
              />
              <p className="text-xs text-slate-400 mt-1">
                Lý do này sẽ được ghi vào nhật ký kiểm toán giá (PriceAuditLog) để phục vụ giải trình.
              </p>
            </div>
          )}
        </div>

        {/* Section 3: Đặc thù F&B & Dinh dưỡng */}
        <div className="space-y-4">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 border-b border-slate-100 pb-1.5">
            3. Đặc thù F&B, Dinh dưỡng & Bảo quản
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Input
                label="Hạn sử dụng khuyến nghị"
                placeholder="VD: 24 giờ / 2 ngày"
                value={formData.shelf_life}
                onChange={(e) => setFormData({ ...formData, shelf_life: e.target.value })}
              />
            </div>
            <div>
              <Input
                label="Hướng dẫn bảo quản"
                placeholder="VD: Giữ lạnh 2-6°C"
                value={formData.storage_note}
                onChange={(e) => setFormData({ ...formData, storage_note: e.target.value })}
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-slate-700 mb-1">Thành phần nguyên liệu</label>
              <textarea
                rows={2}
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600"
                placeholder="VD: 100% Táo New Zealand tươi, nước ozone diệt khuẩn..."
                value={formData.ingredients}
                onChange={(e) => setFormData({ ...formData, ingredients: e.target.value })}
              />
            </div>
            <div>
              <Input
                label="Cảnh báo dị ứng (nếu có)"
                placeholder="VD: Sữa bò, hạt ngũ cốc..."
                value={formData.allergens}
                onChange={(e) => setFormData({ ...formData, allergens: e.target.value })}
              />
            </div>
            <div>
              <Input
                label="Thông tin dinh dưỡng / Calo"
                placeholder="VD: ~95 kcal, Vitamin C: 8.4mg"
                value={formData.nutrition_text}
                onChange={(e) => setFormData({ ...formData, nutrition_text: e.target.value })}
              />
            </div>
          </div>
        </div>

        {/* Section 4: Media & Thẻ phân loại */}
        <div className="space-y-4">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 border-b border-slate-100 pb-1.5">
            4. Hình ảnh, Thẻ phân loại & SEO
          </h4>
          <div className="space-y-4">
            {/* Image picker */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">Ảnh đại diện món (Thumbnail)</label>
              <div className="flex items-start gap-4 p-3 bg-slate-50 border border-slate-200 rounded-xl">
                <div className="w-20 h-20 rounded-lg bg-white border border-slate-200 flex items-center justify-center overflow-hidden shrink-0 text-2xl shadow-2xs">
                  {formData.thumbnail ? (
                    <img
                      src={formData.thumbnail}
                      alt="Thumbnail Preview"
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLElement).style.display = 'none';
                      }}
                    />
                  ) : (
                    <span>🥑</span>
                  )}
                </div>
                <div className="flex-1 space-y-2">
                  <Input
                    placeholder="/uploads/products/... hoặc URL ảnh"
                    value={formData.thumbnail}
                    onChange={(e) => setFormData({ ...formData, thumbnail: e.target.value })}
                  />
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      onClick={() => setIsMediaModalOpen(true)}
                    >
                      🖼️ Chọn từ Thư viện ảnh / Tải lên
                    </Button>
                    {formData.thumbnail && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => setFormData({ ...formData, thumbnail: '' })}
                      >
                        Xóa ảnh
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <Input
              label="Thẻ phân loại (cách nhau bằng dấu phẩy)"
              placeholder="organic, fresh, detox, best-seller"
              value={formData.tags}
              onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
            />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Tiêu đề SEO (tùy chọn)"
                placeholder="Táo New Zealand tươi giòn | Mộc Healthy"
                value={formData.seo_title}
                onChange={(e) => setFormData({ ...formData, seo_title: e.target.value })}
              />
              <Input
                label="Mô tả SEO (tùy chọn)"
                placeholder="Mô tả ngắn gọn hiển thị trên Google..."
                value={formData.seo_description}
                onChange={(e) => setFormData({ ...formData, seo_description: e.target.value })}
              />
            </div>
          </div>
        </div>
      </form>

      {/* Media Library Picker Modal */}
      <MediaLibraryModal
        isOpen={isMediaModalOpen}
        onClose={() => setIsMediaModalOpen(false)}
        onSelect={(media) => {
          setFormData((prev) => ({ ...prev, thumbnail: media.url }));
          setIsMediaModalOpen(false);
        }}
        folder="products"
      />
    </Drawer>
  );
};
