'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { ProtectedRoute } from '../../components/ProtectedRoute';
import { AdminShell } from '../../components/shell/AdminShell';
import {
  StatCard,
  Button,
  Input,
  Select,
  Badge,
  EmptyState,
  ErrorState,
  Skeleton,
  ConfirmDialog,
} from '@moc-healthy/ui';
import { promotionsApi, productsApi, categoriesApi } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';
import {
  Promotion,
  PromotionType,
  PromotionStatus,
  Product,
  Category,
} from '@moc-healthy/contracts';
import { PromotionFormDrawer } from '../../components/promotions/PromotionFormDrawer';
import { PromotionCalculatorModal } from '../../components/promotions/PromotionCalculatorModal';

export default function PromotionsPage() {
  const { hasPermission } = useAuth();
  const canManage = hasPermission('campaign.create');

  // State: Data
  const [promotions, setPromotions] = useState<Promotion[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [selectedType, setSelectedType] = useState<string>('ALL');

  // Modals & Drawers
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isCalculatorOpen, setIsCalculatorOpen] = useState(false);
  const [selectedPromotionForEdit, setSelectedPromotionForEdit] = useState<Promotion | null>(null);

  // Deletion confirm
  const [promotionToDelete, setPromotionToDelete] = useState<Promotion | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Copied feedback
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  // Load data
  const loadData = useCallback(async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const [promosRes, prodsRes, catsRes] = await Promise.all([
        promotionsApi.list({
          status: selectedStatus === 'ALL' ? undefined : selectedStatus,
          type: selectedType === 'ALL' ? undefined : selectedType,
          q: searchQuery.trim() || undefined,
          page_size: 100,
        }),
        productsApi.list({ page_size: 100 }),
        categoriesApi.list(),
      ]);
      setPromotions(promosRes.items || []);
      setProducts(prodsRes.items || []);
      setCategories(catsRes || []);
    } catch (err: any) {
      console.error('Failed to load promotions:', err);
      setErrorMessage(err.message || 'Không thể tải danh sách chương trình khuyến mãi');
    } finally {
      setLoading(false);
    }
  }, [selectedStatus, selectedType, searchQuery]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Handle status toggle
  const handleToggleStatus = async (promo: Promotion) => {
    const nextStatus: PromotionStatus = promo.status === 'ACTIVE' ? 'PAUSED' : 'ACTIVE';
    try {
      await promotionsApi.updateStatus(promo.id, nextStatus);
      setPromotions((prev) =>
        prev.map((p) => (p.id === promo.id ? { ...p, status: nextStatus } : p))
      );
    } catch (err: any) {
      alert('Cập nhật trạng thái thất bại: ' + (err.message || 'Lỗi server'));
    }
  };

  // Handle delete
  const handleDeleteConfirm = async () => {
    if (!promotionToDelete) return;
    setIsDeleting(true);
    try {
      await promotionsApi.delete(promotionToDelete.id);
      setPromotions((prev) => prev.filter((p) => p.id !== promotionToDelete.id));
      setPromotionToDelete(null);
    } catch (err: any) {
      alert('Xóa khuyến mãi thất bại: ' + (err.message || 'Lỗi'));
    } finally {
      setIsDeleting(false);
    }
  };

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const formatVnd = (val?: number | null) => {
    if (val === undefined || val === null) return '—';
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val);
  };

  // Stats
  const activeCount = promotions.filter((p) => p.status === 'ACTIVE').length;
  const totalUsages = promotions.reduce((acc, p) => acc + (p.usage_count || 0), 0);
  const voucherCount = promotions.filter((p) => Boolean(p.code)).length;

  const getTypeBadge = (type: PromotionType) => {
    switch (type) {
      case 'PERCENT_DISCOUNT':
        return <Badge variant="success">Giảm theo %</Badge>;
      case 'FIXED_DISCOUNT':
        return <Badge variant="info">Giảm số tiền</Badge>;
      case 'FLASH_SALE':
        return <Badge variant="danger">⚡ Flash Sale</Badge>;
      case 'BUY_X_GET_Y':
        return <Badge variant="warning">🎁 Mua X Tặng Y</Badge>;
      case 'COMBO':
        return <Badge variant="info">🍱 Combo Gói</Badge>;
      case 'FREE_SHIPPING':
        return <Badge variant="success">🚚 Freeship</Badge>;
      case 'VOUCHER':
        return <Badge variant="neutral">🏷️ Voucher</Badge>;
      default:
        return <Badge variant="neutral">{type}</Badge>;
    }
  };

  const getStatusBadge = (status: PromotionStatus) => {
    switch (status) {
      case 'ACTIVE':
        return <Badge variant="success">🟢 Đang chạy</Badge>;
      case 'PAUSED':
        return <Badge variant="warning">⏸️ Tạm dừng</Badge>;
      case 'EXPIRED':
        return <Badge variant="danger">⏳ Hết hạn</Badge>;
      case 'DRAFT':
        return <Badge variant="neutral">📝 Bản nháp</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  return (
    <ProtectedRoute requiredPermission="campaign.create">
      <AdminShell>
        <div className="space-y-6 max-w-7xl mx-auto pb-12">
          {/* Header */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
            <div>
              <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
                <span>🏷️</span> Quản Lý Khuyến Mãi & Voucher
              </h1>
              <p className="text-xs text-slate-500 mt-1">
                Thiết lập giảm giá %, số tiền, quà tặng Mua X Tặng Y, miễn phí ship và kiểm thử tính toán Authoritative.
              </p>
            </div>

            <div className="flex items-center gap-2.5">
              <Button
                variant="outline"
                onClick={() => setIsCalculatorOpen(true)}
                className="flex items-center gap-1.5 text-xs py-2 shadow-xs"
              >
                <span>🧪</span> Giả Lập Tính Giá (Dry Run)
              </Button>
              {canManage && (
                <Button
                  variant="primary"
                  onClick={() => {
                    setSelectedPromotionForEdit(null);
                    setIsDrawerOpen(true);
                  }}
                  className="flex items-center gap-1.5 text-xs py-2 shadow-xs"
                >
                  <span>+</span> Tạo Khuyến Mãi Mới
                </Button>
              )}
            </div>
          </div>

          {/* Quick Metrics */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Tổng Chương Trình"
              value={String(promotions.length)}
              change="Toàn bộ hệ thống"
              icon="📊"
            />
            <StatCard
              title="Đang Kích Hoạt"
              value={String(activeCount)}
              change="Sẵn sàng áp dụng"
              icon="🟢"
            />
            <StatCard
              title="Lượt Đã Áp Dụng"
              value={String(totalUsages)}
              change="Đơn hàng hưởng ưu đãi"
              icon="🛍️"
            />
            <StatCard
              title="Mã Voucher Có Code"
              value={String(voucherCount)}
              change="Khách nhập thủ công"
              icon="🎟️"
            />
          </div>

          {/* Filters & Search */}
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
            <div className="flex-1 flex flex-col sm:flex-row gap-2.5">
              <div className="w-full sm:w-72">
                <Input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Tìm theo tên CTKM hoặc mã Voucher..."
                  className="text-xs"
                />
              </div>

              <div className="w-full sm:w-48">
                <Select
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value)}
                  options={[
                    { value: 'ALL', label: 'Tất cả loại hình' },
                    { value: 'PERCENT_DISCOUNT', label: 'Giảm theo phần trăm' },
                    { value: 'FIXED_DISCOUNT', label: 'Giảm số tiền cố định' },
                    { value: 'FLASH_SALE', label: 'Flash Sale' },
                    { value: 'BUY_X_GET_Y', label: 'Mua X Tặng Y' },
                    { value: 'FREE_SHIPPING', label: 'Freeship vận chuyển' },
                    { value: 'VOUCHER', label: 'Voucher nhập mã' },
                  ]}
                />
              </div>

              <div className="w-full sm:w-44">
                <Select
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                  options={[
                    { value: 'ALL', label: 'Tất cả trạng thái' },
                    { value: 'ACTIVE', label: '🟢 Đang chạy' },
                    { value: 'PAUSED', label: '⏸️ Tạm dừng' },
                    { value: 'EXPIRED', label: '⏳ Hết hạn' },
                    { value: 'DRAFT', label: '📝 Bản nháp' },
                  ]}
                />
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={loadData}
              className="text-xs py-2 shrink-0"
              title="Làm mới danh sách"
            >
              🔄 Tải lại
            </Button>
          </div>

          {/* Feedback banner */}
          {copiedCode && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl flex items-center justify-between animate-in fade-in">
              <span>✅ Đã sao chép mã voucher <strong>{copiedCode}</strong> vào clipboard!</span>
            </div>
          )}

          {/* Promotion Table */}
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
            {loading ? (
              <div className="p-8 space-y-4">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
              </div>
            ) : errorMessage ? (
              <div className="p-8">
                <ErrorState message={errorMessage} onRetry={loadData} />
              </div>
            ) : promotions.length === 0 ? (
              <div className="p-12">
                <EmptyState
                  title="Chưa có chương trình khuyến mãi nào"
                  description="Hãy bắt đầu tạo chương trình ưu đãi đầu tiên để thu hút khách hàng và gia tăng đơn hàng."
                  actionText="+ Tạo Khuyến Mãi Đầu Tiên"
                  onAction={() => {
                    setSelectedPromotionForEdit(null);
                    setIsDrawerOpen(true);
                  }}
                />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-600">
                  <thead className="bg-slate-50/80 text-[11px] uppercase tracking-wider text-slate-500 font-semibold border-b border-slate-200">
                    <tr>
                      <th className="py-3.5 px-4">Tên & Mã Voucher</th>
                      <th className="py-3.5 px-4">Loại & Mức Ưu Đãi</th>
                      <th className="py-3.5 px-4">Điều Kiện Áp Dụng</th>
                      <th className="py-3.5 px-4">Thời Gian Hiệu Lực</th>
                      <th className="py-3.5 px-4">Lượt Dùng</th>
                      <th className="py-3.5 px-4">Trạng Thái</th>
                      <th className="py-3.5 px-4 text-right">Thao Tác</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {promotions.map((p) => {
                      const startDate = new Date(p.start_at).toLocaleDateString('vi-VN');
                      const endDate = new Date(p.end_at).toLocaleDateString('vi-VN');
                      const isExpired = new Date(p.end_at) < new Date();

                      return (
                        <tr key={p.id} className="hover:bg-slate-50/60 transition-colors">
                          {/* Col 1: Title & Code */}
                          <td className="py-3.5 px-4">
                            <div className="font-semibold text-slate-900 text-sm">
                              {p.title}
                            </div>
                            <div className="flex items-center gap-1.5 mt-1">
                              {p.code ? (
                                <button
                                  type="button"
                                  onClick={() => handleCopyCode(p.code!)}
                                  className="inline-flex items-center gap-1 font-mono font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 px-2 py-0.5 rounded text-[11px] hover:bg-emerald-100 transition-colors"
                                  title="Nhấp để copy mã"
                                >
                                  <span>🏷️ {p.code}</span>
                                  <span className="text-[10px] text-emerald-600 font-sans">📋</span>
                                </button>
                              ) : (
                                <span className="text-[11px] text-slate-400 italic">
                                  Tự động áp dụng (Toàn sàn)
                                </span>
                              )}
                              {p.stackable && (
                                <span className="bg-purple-50 text-purple-700 border border-purple-200 text-[10px] px-1.5 py-0.2 rounded font-medium">
                                  Gộp được
                                </span>
                              )}
                            </div>
                            {p.description && (
                              <p className="text-[11px] text-slate-500 mt-1 line-clamp-1 max-w-xs">
                                {p.description}
                              </p>
                            )}
                          </td>

                          {/* Col 2: Type & Value */}
                          <td className="py-3.5 px-4">
                            <div className="space-y-1">
                              <div>{getTypeBadge(p.type)}</div>
                              <div className="font-bold text-slate-800 text-xs">
                                {p.type === 'PERCENT_DISCOUNT' || p.type === 'FLASH_SALE'
                                  ? `Giảm ${p.value}%`
                                  : p.type === 'FREE_SHIPPING'
                                  ? 'Miễn phí ship'
                                  : p.type === 'BUY_X_GET_Y'
                                  ? `Mua ${p.buy_x_get_y_config?.buy_quantity || 2} tặng ${
                                      p.buy_x_get_y_config?.get_quantity || 1
                                    }`
                                  : `Giảm ${formatVnd(p.value)}`}
                              </div>
                            </div>
                          </td>

                          {/* Col 3: Conditions */}
                          <td className="py-3.5 px-4 space-y-1">
                            {p.min_order_value ? (
                              <div className="text-[11px]">
                                <span className="text-slate-400">Đơn từ: </span>
                                <strong className="text-slate-700">{formatVnd(p.min_order_value)}</strong>
                              </div>
                            ) : (
                              <div className="text-[11px] text-slate-400">Không yêu cầu đơn tối thiểu</div>
                            )}

                            {p.max_discount && (
                              <div className="text-[11px]">
                                <span className="text-slate-400">Tối đa: </span>
                                <strong className="text-slate-700">{formatVnd(p.max_discount)}</strong>
                              </div>
                            )}

                            <div className="text-[11px] text-slate-500">
                              Phạm vi:{' '}
                              {p.product_scope === 'ALL'
                                ? 'Toàn bộ SP'
                                : p.product_scope === 'SPECIFIC_PRODUCTS'
                                ? `${p.applicable_product_ids?.length || 0} sản phẩm chọn`
                                : `${p.applicable_category_ids?.length || 0} danh mục`}
                            </div>
                          </td>

                          {/* Col 4: Validity */}
                          <td className="py-3.5 px-4">
                            <div className="text-[11px] text-slate-700">
                              <span className="block">{startDate}</span>
                              <span className="text-slate-400 text-[10px]">đến</span>
                              <span className="block font-medium">{endDate}</span>
                            </div>
                            {isExpired && (
                              <span className="text-[10px] text-rose-600 font-semibold block mt-0.5">
                                Đã kết thúc
                              </span>
                            )}
                          </td>

                          {/* Col 5: Usage */}
                          <td className="py-3.5 px-4">
                            <div className="font-semibold text-slate-800">
                              {p.usage_count}
                              <span className="text-slate-400 font-normal">
                                {p.usage_limit ? ` / ${p.usage_limit}` : ' lượt (vô hạn)'}
                              </span>
                            </div>
                            {p.usage_limit && (
                              <div className="w-20 bg-slate-100 rounded-full h-1.5 mt-1 overflow-hidden">
                                <div
                                  className="bg-emerald-500 h-1.5 rounded-full"
                                  style={{
                                    width: `${Math.min(
                                      100,
                                      Math.round(((p.usage_count || 0) / p.usage_limit) * 100)
                                    )}%`,
                                  }}
                                />
                              </div>
                            )}
                          </td>

                          {/* Col 6: Status */}
                          <td className="py-3.5 px-4">
                            <div className="space-y-1">
                              {getStatusBadge(p.status)}
                              {canManage && (
                                <button
                                  type="button"
                                  onClick={() => handleToggleStatus(p)}
                                  className="text-[11px] text-slate-500 hover:text-slate-900 block underline cursor-pointer"
                                >
                                  {p.status === 'ACTIVE' ? 'Tạm dừng' : 'Bật lại'}
                                </button>
                              )}
                            </div>
                          </td>

                          {/* Col 7: Actions */}
                          <td className="py-3.5 px-4 text-right space-x-1.5">
                            {canManage && (
                              <>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => {
                                    setSelectedPromotionForEdit(p);
                                    setIsDrawerOpen(true);
                                  }}
                                  className="text-xs py-1"
                                >
                                  Sửa
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => setPromotionToDelete(p)}
                                  className="text-xs py-1 text-red-600 hover:text-red-700 hover:bg-red-50"
                                >
                                  Xóa
                                </Button>
                              </>
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
        </div>

        {/* Promotion Form Drawer */}
        <PromotionFormDrawer
          isOpen={isDrawerOpen}
          onClose={() => {
            setIsDrawerOpen(false);
            setSelectedPromotionForEdit(null);
          }}
          onSuccess={loadData}
          promotionToEdit={selectedPromotionForEdit}
          products={products}
          categories={categories}
        />

        {/* Promotion Calculator Dry Run Modal */}
        <PromotionCalculatorModal
          isOpen={isCalculatorOpen}
          onClose={() => setIsCalculatorOpen(false)}
          products={products}
        />

        {/* Confirm Delete Dialog */}
        <ConfirmDialog
          isOpen={Boolean(promotionToDelete)}
          onClose={() => setPromotionToDelete(null)}
          onConfirm={handleDeleteConfirm}
          title="Xác nhận xóa khuyến mãi"
          message={`Bạn có chắc chắn muốn xóa chương trình "${promotionToDelete?.title}"? Hành động này không thể hoàn tác.`}
          confirmText="Xóa vĩnh viễn"
          cancelText="Hủy"
          isDestructive
          isLoading={isDeleting}
        />
      </AdminShell>
    </ProtectedRoute>
  );
}
