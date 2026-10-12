'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Button,
  Input,
  Select,
  Badge,
  DataTable,
  Pagination,
  EmptyState,
  ErrorState,
  Skeleton,
  ConfirmDialog,
  StatCard,
  Card,
} from '@moc-healthy/ui';
import { Product, Category, ProductStatus } from '@moc-healthy/contracts';
import { AdminShell } from '../../components/shell/AdminShell';
import { PageHeader } from '../../components/shell/PageHeader';
import { useAuth } from '../../context/AuthContext';
import { productsApi, categoriesApi } from '../../lib/api';
import { ProductFormDrawer } from '../../components/products/ProductFormDrawer';
import { PriceHistoryDialog } from '../../components/products/PriceHistoryDialog';
import { CategoryManagerDialog } from '../../components/products/CategoryManagerDialog';
import { MediaLibraryModal } from '../../components/media/MediaLibraryModal';

export default function ProductsPage() {
  const { hasPermission } = useAuth();
  const canWrite = hasPermission('product.write');

  // State: Data
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  // State: Filters & Pagination
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [selectedSort, setSelectedSort] = useState('created_at_desc');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  // State: UI Status
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // State: Selection for Bulk Actions
  const [selectedProductIds, setSelectedProductIds] = useState<string[]>([]);
  const [isBulkUpdating, setIsBulkUpdating] = useState(false);

  // State: Drawers & Dialogs
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [productToEdit, setProductToEdit] = useState<Product | null>(null);

  const [isPriceHistoryOpen, setIsPriceHistoryOpen] = useState(false);
  const [selectedProductForHistory, setSelectedProductForHistory] = useState<Product | null>(null);

  const [isCategoryManagerOpen, setIsCategoryManagerOpen] = useState(false);
  const [isMediaLibraryOpen, setIsMediaLibraryOpen] = useState(false);

  const [confirmDeleteTarget, setConfirmDeleteTarget] = useState<Product | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Fetch categories
  const loadCategories = useCallback(async () => {
    try {
      const data = await categoriesApi.list(true);
      setCategories(data);
    } catch (err: any) {
      console.error('Không thể tải danh mục:', err);
    }
  }, []);

  // Fetch products
  const loadProducts = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const res = await productsApi.list({
        q: searchTerm.trim() || undefined,
        category_id: selectedCategory || undefined,
        status: selectedStatus || undefined,
        sort_by: selectedSort,
        page: currentPage,
        page_size: pageSize,
      });
      setProducts(res.items);
      setTotalCount(res.total);
      setTotalPages(res.total_pages);
    } catch (err: any) {
      setErrorMessage(err.message || 'Không thể kết nối đến máy chủ lấy danh sách sản phẩm');
    } finally {
      setIsLoading(false);
    }
  }, [searchTerm, selectedCategory, selectedStatus, selectedSort, currentPage, pageSize]);

  // Initial load
  useEffect(() => {
    loadCategories();
  }, [loadCategories]);

  useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  // Helper formatting
  const formatVND = (val?: number | null) => {
    if (val === null || val === undefined) return '—';
    return `${Number(val).toLocaleString('vi-VN')} đ`;
  };

  const getStatusBadge = (status: ProductStatus) => {
    switch (status) {
      case 'ACTIVE':
        return <Badge variant="success">Đang bán</Badge>;
      case 'OUT_OF_STOCK':
        return <Badge variant="danger">Hết hàng</Badge>;
      case 'DRAFT':
        return <Badge variant="warning">Bản nháp</Badge>;
      case 'HIDDEN':
        return <Badge variant="neutral">Ẩn</Badge>;
      case 'ARCHIVED':
        return <Badge variant="neutral">Đã lưu trữ</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  // Bulk status update
  const handleBulkStatusChange = async (newStatus: ProductStatus) => {
    if (selectedProductIds.length === 0) return;
    setIsBulkUpdating(true);
    try {
      await productsApi.bulkUpdateStatus(selectedProductIds, newStatus);
      setSelectedProductIds([]);
      loadProducts();
    } catch (err: any) {
      alert(err.message || 'Lỗi cập nhật trạng thái hàng loạt');
    } finally {
      setIsBulkUpdating(false);
    }
  };

  // Delete / Archive single product
  const handleConfirmDelete = async () => {
    if (!confirmDeleteTarget) return;
    setIsDeleting(true);
    try {
      await productsApi.delete(confirmDeleteTarget.id, false);
      setConfirmDeleteTarget(null);
      loadProducts();
    } catch (err: any) {
      alert(err.message || 'Lỗi khi lưu trữ sản phẩm');
    } finally {
      setIsDeleting(false);
    }
  };

  // Selection handlers
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedProductIds(products.map((p) => p.id));
    } else {
      setSelectedProductIds([]);
    }
  };

  const handleSelectRow = (productId: string, checked: boolean) => {
    if (checked) {
      setSelectedProductIds((prev) => [...prev, productId]);
    } else {
      setSelectedProductIds((prev) => prev.filter((id) => id !== productId));
    }
  };

  // Stat metrics
  const activeCount = products.filter((p) => p.status === 'ACTIVE').length;
  const outOfStockCount = products.filter((p) => p.status === 'OUT_OF_STOCK').length;

  return (
    <AdminShell requiredPermission="product.read">
      {/* 1. Header & Actions */}
      <PageHeader
        title="Quản lý Sản phẩm (Products)"
        subtitle="Quản lý danh mục F&B Mộc Healthy, bảng giá niêm yết, công thức dinh dưỡng và lịch sử kiểm toán giá"
        breadcrumbs={[{ label: 'Thương mại' }, { label: 'Sản phẩm' }]}
        actions={
          <div className="flex gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setIsMediaLibraryOpen(true)}
            >
              🖼️ Thư viện Media
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setIsCategoryManagerOpen(true)}
            >
              🏷️ Quản lý danh mục ({categories.length})
            </Button>
            {canWrite && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => {
                  setProductToEdit(null);
                  setIsDrawerOpen(true);
                }}
              >
                + Thêm sản phẩm mới
              </Button>
            )}
          </div>
        }
      />

      {/* 2. Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard
          title="Tổng số sản phẩm"
          value={totalCount}
          period="Trong cơ sở dữ liệu"
        />
        <StatCard
          title="Đang mở bán"
          value={activeCount}
          period="Hiển thị trên storefront"
          changeType="positive"
        />
        <StatCard
          title="Hết hàng / Tạm ngừng"
          value={outOfStockCount}
          period="Cần nhập lô mới"
          changeType={outOfStockCount > 0 ? 'negative' : 'neutral'}
        />
        <StatCard
          title="Danh mục F&B"
          value={categories.length}
          period="Nhóm thực phẩm & đồ uống"
        />
      </div>

      {/* 3. Filter & Search Bar */}
      <Card className="mb-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <Input
            placeholder="Tìm theo tên sản phẩm hoặc mã SKU..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
          />

          <Select
            options={[
              { label: 'Tất cả danh mục', value: '' },
              ...categories.map((c) => ({ label: c.name, value: c.id })),
            ]}
            value={selectedCategory}
            onChange={(e) => {
              setSelectedCategory(e.target.value);
              setCurrentPage(1);
            }}
          />

          <Select
            options={[
              { label: 'Tất cả trạng thái', value: '' },
              { label: 'Đang bán (ACTIVE)', value: 'ACTIVE' },
              { label: 'Hết hàng (OUT_OF_STOCK)', value: 'OUT_OF_STOCK' },
              { label: 'Bản nháp (DRAFT)', value: 'DRAFT' },
              { label: 'Ẩn (HIDDEN)', value: 'HIDDEN' },
              { label: 'Lưu trữ (ARCHIVED)', value: 'ARCHIVED' },
            ]}
            value={selectedStatus}
            onChange={(e) => {
              setSelectedStatus(e.target.value);
              setCurrentPage(1);
            }}
          />

          <Select
            options={[
              { label: 'Mới nhất trước', value: 'created_at_desc' },
              { label: 'Cũ nhất trước', value: 'created_at_asc' },
              { label: 'Giá tăng dần', value: 'price_asc' },
              { label: 'Giá giảm dần', value: 'price_desc' },
              { label: 'Tên A → Z', value: 'name_asc' },
            ]}
            value={selectedSort}
            onChange={(e) => {
              setSelectedSort(e.target.value);
              setCurrentPage(1);
            }}
          />
        </div>

        {(searchTerm || selectedCategory || selectedStatus) && (
          <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>Đang áp dụng bộ lọc</span>
            <button
              type="button"
              onClick={() => {
                setSearchTerm('');
                setSelectedCategory('');
                setSelectedStatus('');
                setCurrentPage(1);
              }}
              className="text-emerald-700 hover:text-emerald-900 font-medium underline cursor-pointer"
            >
              Đặt lại bộ lọc
            </button>
          </div>
        )}
      </Card>

      {/* 4. Bulk Action Bar */}
      {selectedProductIds.length > 0 && canWrite && (
        <div className="mb-4 p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl flex flex-wrap items-center justify-between gap-3 text-sm animate-fadeIn">
          <div className="flex items-center gap-2 text-emerald-900 font-medium">
            <span>Đã chọn <strong>{selectedProductIds.length}</strong> sản phẩm</span>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              isLoading={isBulkUpdating}
              onClick={() => handleBulkStatusChange('ACTIVE')}
            >
              Chuyển sang Đang bán
            </Button>
            <Button
              variant="secondary"
              size="sm"
              isLoading={isBulkUpdating}
              onClick={() => handleBulkStatusChange('OUT_OF_STOCK')}
            >
              Báo Hết hàng
            </Button>
            <Button
              variant="danger"
              size="sm"
              isLoading={isBulkUpdating}
              onClick={() => handleBulkStatusChange('ARCHIVED')}
            >
              Lưu trữ hàng loạt
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedProductIds([])}
            >
              Bỏ chọn
            </Button>
          </div>
        </div>
      )}

      {/* 5. Main Content: Table, Empty, Error, Loading */}
      {isLoading ? (
        <Card className="space-y-3 p-6">
          <Skeleton height="40px" />
          <Skeleton height="50px" />
          <Skeleton height="50px" />
          <Skeleton height="50px" />
          <Skeleton height="50px" />
        </Card>
      ) : errorMessage ? (
        <ErrorState
          title="Không thể tải dữ liệu sản phẩm"
          message={errorMessage}
          onRetry={loadProducts}
        />
      ) : products.length === 0 ? (
        <EmptyState
          title="Không tìm thấy sản phẩm nào"
          description={
            searchTerm || selectedCategory || selectedStatus
              ? 'Không có sản phẩm nào phù hợp với điều kiện tìm kiếm và bộ lọc hiện tại.'
              : 'Chưa có sản phẩm nào trong hệ thống Mộc Healthy. Hãy tạo sản phẩm F&B đầu tiên!'
          }
          icon="🥑"
          actionText={canWrite ? '+ Thêm sản phẩm mới' : undefined}
          onAction={
            canWrite
              ? () => {
                  setProductToEdit(null);
                  setIsDrawerOpen(true);
                }
              : undefined
          }
        />
      ) : (
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-slate-200/90 shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-600">
                <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase">
                  <tr>
                    {canWrite && (
                      <th className="px-4 py-3 w-10 text-center">
                        <input
                          type="checkbox"
                          checked={
                            products.length > 0 && selectedProductIds.length === products.length
                          }
                          onChange={(e) => handleSelectAll(e.target.checked)}
                          className="w-4 h-4 text-emerald-600 rounded"
                        />
                      </th>
                    )}
                    <th className="px-4 py-3">Sản phẩm & SKU</th>
                    <th className="px-4 py-3">Danh mục</th>
                    <th className="px-4 py-3">Giá niêm yết / KM</th>
                    <th className="px-4 py-3 text-center">Đơn vị</th>
                    <th className="px-4 py-3">Trạng thái</th>
                    <th className="px-4 py-3 text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {products.map((prod) => {
                    const isSelected = selectedProductIds.includes(prod.id);
                    const hasDiscount = prod.sale_price !== null && prod.sale_price !== undefined && prod.sale_price < prod.base_price;
                    const discountPercent = hasDiscount
                      ? Math.round(((prod.base_price - prod.sale_price!) / prod.base_price) * 100)
                      : 0;

                    return (
                      <tr
                        key={prod.id}
                        className={`hover:bg-slate-50/70 transition-colors ${
                          isSelected ? 'bg-emerald-50/40' : ''
                        }`}
                      >
                        {canWrite && (
                          <td className="px-4 py-3 text-center">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={(e) => handleSelectRow(prod.id, e.target.checked)}
                              className="w-4 h-4 text-emerald-600 rounded"
                            />
                          </td>
                        )}
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-emerald-50 border border-emerald-100 flex items-center justify-center text-lg shrink-0 overflow-hidden">
                              {prod.thumbnail ? (
                                <img
                                  src={prod.thumbnail}
                                  alt={prod.name}
                                  className="w-full h-full object-cover"
                                  onError={(e) => {
                                    // Fallback to emoji if image cannot be loaded
                                    (e.target as HTMLElement).style.display = 'none';
                                  }}
                                />
                              ) : (
                                <span>🥑</span>
                              )}
                            </div>
                            <div>
                              <div className="font-semibold text-slate-900 flex items-center gap-1.5">
                                <span>{prod.name}</span>
                                {prod.featured && (
                                  <span title="Sản phẩm nổi bật / Best seller">⭐</span>
                                )}
                              </div>
                              <div className="flex items-center gap-2 mt-0.5">
                                <span className="font-mono text-xs text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                                  {prod.sku}
                                </span>
                                {prod.shelf_life && (
                                  <span className="text-xs text-slate-400">
                                    HSD: {prod.shelf_life}
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          {prod.category ? (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700">
                              {prod.category.name}
                            </span>
                          ) : (
                            <span className="text-xs text-slate-400 italic">Chưa phân loại</span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <div>
                            {hasDiscount ? (
                              <div className="flex items-baseline gap-1.5">
                                <span className="font-semibold text-rose-600">
                                  {formatVND(prod.sale_price)}
                                </span>
                                <span className="line-through text-xs text-slate-400">
                                  {formatVND(prod.base_price)}
                                </span>
                                <span className="text-xs font-bold text-rose-500 bg-rose-50 px-1 rounded">
                                  -{discountPercent}%
                                </span>
                              </div>
                            ) : (
                              <span className="font-semibold text-slate-900">
                                {formatVND(prod.base_price)}
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-center text-xs font-medium text-slate-600">
                          {prod.unit}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          {getStatusBadge(prod.status)}
                        </td>
                        <td className="px-4 py-3 text-right whitespace-nowrap">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              type="button"
                              onClick={() => {
                                setSelectedProductForHistory(prod);
                                setIsPriceHistoryOpen(true);
                              }}
                              className="text-xs text-slate-600 hover:text-slate-900 font-medium px-2 py-1 rounded hover:bg-slate-100 transition-colors"
                              title="Xem lịch sử kiểm toán giá"
                            >
                              🏷️ Giá
                            </button>
                            {canWrite && (
                              <>
                                <button
                                  type="button"
                                  onClick={() => {
                                    setProductToEdit(prod);
                                    setIsDrawerOpen(true);
                                  }}
                                  className="text-xs text-emerald-700 hover:text-emerald-900 font-medium px-2 py-1 rounded hover:bg-emerald-50 transition-colors"
                                >
                                  Sửa
                                </button>
                                <button
                                  type="button"
                                  onClick={() => setConfirmDeleteTarget(prod)}
                                  className="text-xs text-red-600 hover:text-red-800 font-medium px-2 py-1 rounded hover:bg-red-50 transition-colors"
                                  title="Lưu trữ sản phẩm"
                                >
                                  Lưu trữ
                                </button>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination footer */}
            <div className="p-4 border-t border-slate-100 flex items-center justify-between">
              <span className="text-xs text-slate-500">
                Hiển thị <strong>{products.length}</strong> / <strong>{totalCount}</strong> sản phẩm
              </span>
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={(page) => setCurrentPage(page)}
              />
            </div>
          </div>
        </div>
      )}

      {/* 6. Product Form Drawer (Create / Edit) */}
      <ProductFormDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        onSuccess={() => {
          loadProducts();
          loadCategories();
        }}
        productToEdit={productToEdit}
        categories={categories}
      />

      {/* 7. Price History Dialog */}
      <PriceHistoryDialog
        isOpen={isPriceHistoryOpen}
        onClose={() => setIsPriceHistoryOpen(false)}
        product={selectedProductForHistory}
      />

      {/* 8. Category Manager Dialog */}
      <CategoryManagerDialog
        isOpen={isCategoryManagerOpen}
        onClose={() => setIsCategoryManagerOpen(false)}
        categories={categories}
        onRefresh={() => {
          loadCategories();
          loadProducts();
        }}
        canWrite={canWrite}
      />

      {/* 9. Confirm Archive Dialog */}
      <ConfirmDialog
        isOpen={Boolean(confirmDeleteTarget)}
        onClose={() => setConfirmDeleteTarget(null)}
        onConfirm={handleConfirmDelete}
        title="Lưu trữ sản phẩm?"
        message={`Bạn có chắc muốn chuyển sản phẩm "${confirmDeleteTarget?.name}" sang trạng thái Lưu trữ (ARCHIVED)? Sản phẩm sẽ không còn hiển thị bán trên Storefront nhưng dữ liệu đơn hàng và lịch sử giá vẫn được bảo tồn.`}
        confirmText="Xác nhận lưu trữ"
        cancelText="Hủy"
        isDestructive={false}
        isLoading={isDeleting}
      />

      {/* 10. Standalone Media Library Modal */}
      <MediaLibraryModal
        isOpen={isMediaLibraryOpen}
        onClose={() => setIsMediaLibraryOpen(false)}
        folder="products"
      />
    </AdminShell>
  );
}
