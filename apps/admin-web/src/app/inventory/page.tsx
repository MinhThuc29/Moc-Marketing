'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { ProtectedRoute } from '../../components/ProtectedRoute';
import { AdminShell } from '../../components/shell/AdminShell';
import {
  StatCard,
  Button,
  Input,
  Badge,
  EmptyState,
  ErrorState,
  Skeleton,
} from '@moc-healthy/ui';
import { inventoryApi } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';
import {
  InventoryOverview,
  ProductInventorySummary,
  InventoryBatch,
  InventoryMovement,
  ExpiryAlertItem,
} from '@moc-healthy/contracts';
import { ReceiveBatchModal } from '../../components/inventory/ReceiveBatchModal';
import { AdjustStockModal } from '../../components/inventory/AdjustStockModal';
import { FefoSimulatorModal } from '../../components/inventory/FefoSimulatorModal';

type InventoryTab = 'products' | 'batches' | 'alerts' | 'ledger';

export default function InventoryPage() {
  const { hasPermission } = useAuth();
  const canWrite = hasPermission('inventory.write');

  // Active tab
  const [activeTab, setActiveTab] = useState<InventoryTab>('products');

  // Overview data
  const [overview, setOverview] = useState<InventoryOverview | null>(null);
  const [loadingOverview, setLoadingOverview] = useState(true);

  // Tab 1: Product Summaries
  const [products, setProducts] = useState<ProductInventorySummary[]>([]);
  const [loadingProducts, setLoadingProducts] = useState(false);
  const [productSearch, setProductSearch] = useState('');
  const [lowStockOnly, setLowStockOnly] = useState(false);
  const [expiringOnly, setExpiringOnly] = useState(false);

  // Tab 2: Batches
  const [batches, setBatches] = useState<InventoryBatch[]>([]);
  const [loadingBatches, setLoadingBatches] = useState(false);
  const [batchSearch, setBatchSearch] = useState('');
  const [batchStatusFilter, setBatchStatusFilter] = useState('');
  const [batchExpiryDays, setBatchExpiryDays] = useState<string>('');

  // Tab 3: Expiry Alerts
  const [alerts, setAlerts] = useState<ExpiryAlertItem[]>([]);
  const [loadingAlerts, setLoadingAlerts] = useState(false);

  // Tab 4: Ledger Movements
  const [movements, setMovements] = useState<InventoryMovement[]>([]);
  const [loadingMovements, setLoadingMovements] = useState(false);
  const [movementTypeFilter, setMovementTypeFilter] = useState('');

  // Modals state
  const [isReceiveModalOpen, setIsReceiveModalOpen] = useState(false);
  const [receiveInitialProdId, setReceiveInitialProdId] = useState<string | undefined>(undefined);
  const [adjustBatch, setAdjustBatch] = useState<InventoryBatch | null>(null);
  const [isFefoModalOpen, setIsFefoModalOpen] = useState(false);
  const [fefoInitialProdId, setFefoInitialProdId] = useState<string | undefined>(undefined);

  // General error
  const [error, setError] = useState<string | null>(null);

  // Load Overview
  const loadOverview = useCallback(async () => {
    try {
      setLoadingOverview(true);
      const data = await inventoryApi.getOverview();
      setOverview(data);
    } catch (err: any) {
      console.error('Failed to load overview:', err);
    } finally {
      setLoadingOverview(false);
    }
  }, []);

  // Load Products
  const loadProducts = useCallback(async () => {
    try {
      setLoadingProducts(true);
      const data = await inventoryApi.getProductSummaries({
        search: productSearch || undefined,
        low_stock_only: lowStockOnly,
        expiring_soon_only: expiringOnly,
      });
      setProducts(data);
    } catch (err: any) {
      setError(err.message || 'Lỗi tải danh sách sản phẩm');
    } finally {
      setLoadingProducts(false);
    }
  }, [productSearch, lowStockOnly, expiringOnly]);

  // Load Batches
  const loadBatches = useCallback(async () => {
    try {
      setLoadingBatches(true);
      const data = await inventoryApi.listBatches({
        search: batchSearch || undefined,
        status: batchStatusFilter || undefined,
        expiring_within_days: batchExpiryDays ? parseInt(batchExpiryDays) : undefined,
      });
      setBatches(data);
    } catch (err: any) {
      setError(err.message || 'Lỗi tải danh sách lô hàng');
    } finally {
      setLoadingBatches(false);
    }
  }, [batchSearch, batchStatusFilter, batchExpiryDays]);

  // Load Alerts
  const loadAlerts = useCallback(async () => {
    try {
      setLoadingAlerts(true);
      const data = await inventoryApi.getExpiryAlerts();
      setAlerts(data);
    } catch (err: any) {
      setError(err.message || 'Lỗi tải cảnh báo hạn dùng');
    } finally {
      setLoadingAlerts(false);
    }
  }, []);

  // Load Movements
  const loadMovements = useCallback(async () => {
    try {
      setLoadingMovements(true);
      const data = await inventoryApi.listMovements({
        movement_type: movementTypeFilter || undefined,
        page_size: 100,
      });
      setMovements(data);
    } catch (err: any) {
      setError(err.message || 'Lỗi tải sổ cái kho');
    } finally {
      setLoadingMovements(false);
    }
  }, [movementTypeFilter]);

  // Refresh all current tab data
  const refreshCurrentTab = useCallback(() => {
    loadOverview();
    if (activeTab === 'products') loadProducts();
    if (activeTab === 'batches') loadBatches();
    if (activeTab === 'alerts') loadAlerts();
    if (activeTab === 'ledger') loadMovements();
  }, [activeTab, loadOverview, loadProducts, loadBatches, loadAlerts, loadMovements]);

  useEffect(() => {
    loadOverview();
  }, [loadOverview]);

  useEffect(() => {
    if (activeTab === 'products') loadProducts();
    if (activeTab === 'batches') loadBatches();
    if (activeTab === 'alerts') loadAlerts();
    if (activeTab === 'ledger') loadMovements();
  }, [activeTab, loadProducts, loadBatches, loadAlerts, loadMovements]);

  const openReceiveForProduct = (prodId: string) => {
    setReceiveInitialProdId(prodId);
    setIsReceiveModalOpen(true);
  };

  const openFefoForProduct = (prodId: string) => {
    setFefoInitialProdId(prodId);
    setIsFefoModalOpen(true);
  };

  return (
    <ProtectedRoute requiredPermission="inventory.read">
      <AdminShell>
        <div className="space-y-6">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-2xl">📦</span>
                <h1 className="text-xl font-bold text-slate-900">Quản lý Kho & Hạn dùng (FEFO)</h1>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Quản lý tồn kho theo lô sản xuất, tự động cảnh báo cận date và phân bổ xuất kho FEFO cho F&B tươi sạch.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <Button variant="ghost" size="sm" onClick={refreshCurrentTab}>
                🔄 Làm mới
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  setFefoInitialProdId(undefined);
                  setIsFefoModalOpen(true);
                }}
              >
                ⚡ Mô phỏng FEFO
              </Button>
              {canWrite && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => {
                    setReceiveInitialProdId(undefined);
                    setIsReceiveModalOpen(true);
                  }}
                >
                  + Nhập lô hàng mới
                </Button>
              )}
            </div>
          </div>

          {/* Overview Cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <StatCard
              title="Tổng tồn kho"
              value={overview ? `${overview.total_stock_units} phần` : '...'}
              icon="🏢"
              change={overview ? `${overview.total_batches} lô hàng` : undefined}
            />
            <StatCard
              title="Cận date (< 3 ngày)"
              value={overview ? overview.expiring_soon_batches_count : '...'}
              icon="⏰"
              change={
                overview && overview.critical_batches_count > 0
                  ? `Khẩn cấp <24h: ${overview.critical_batches_count}`
                  : undefined
              }
            />
            <StatCard
              title="Đã quá hạn"
              value={overview ? overview.expired_batches_count : '...'}
              icon="⚠️"
              change={overview && overview.expired_batches_count > 0 ? 'Cần xuất hủy' : '0 lô'}
            />
            <StatCard
              title="Dưới định mức"
              value={overview ? overview.low_stock_products_count : '...'}
              icon="📉"
              change="Cần nhập thêm"
            />
            <StatCard
              title="Tổng giá trị vốn"
              value={
                overview
                  ? `${overview.total_inventory_value.toLocaleString('vi-VN')} đ`
                  : '...'
              }
              icon="💰"
            />
          </div>

          {/* Tab Navigation */}
          <div className="border-b border-slate-200">
            <nav className="flex space-x-6 text-xs font-semibold">
              <button
                onClick={() => setActiveTab('products')}
                className={`pb-3 border-b-2 transition ${
                  activeTab === 'products'
                    ? 'border-emerald-600 text-emerald-700'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                🥗 Sản phẩm & Định mức ({products.length})
              </button>
              <button
                onClick={() => setActiveTab('batches')}
                className={`pb-3 border-b-2 transition ${
                  activeTab === 'batches'
                    ? 'border-emerald-600 text-emerald-700'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                📦 Danh sách Lô hàng ({batches.length})
              </button>
              <button
                onClick={() => setActiveTab('alerts')}
                className={`pb-3 border-b-2 transition flex items-center space-x-1.5 ${
                  activeTab === 'alerts'
                    ? 'border-rose-600 text-rose-700'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <span>🚨 Cảnh báo Hạn dùng & Rủi ro</span>
                {overview && overview.expiring_soon_batches_count > 0 && (
                  <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-rose-100 text-rose-700 font-bold">
                    {overview.expiring_soon_batches_count + overview.expired_batches_count}
                  </span>
                )}
              </button>
              <button
                onClick={() => setActiveTab('ledger')}
                className={`pb-3 border-b-2 transition ${
                  activeTab === 'ledger'
                    ? 'border-emerald-600 text-emerald-700'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                📜 Sổ cái Luân chuyển kho
              </button>
            </nav>
          </div>

          {/* TAB 1: PRODUCT STOCK SUMMARIES */}
          {activeTab === 'products' && (
            <div className="space-y-4">
              {/* Filter Bar */}
              <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
                <div className="w-full sm:w-72">
                  <Input
                    type="text"
                    placeholder="Tìm theo tên hoặc SKU..."
                    value={productSearch}
                    onChange={(e) => setProductSearch(e.target.value)}
                  />
                </div>
                <div className="flex flex-wrap items-center gap-3 text-xs">
                  <label className="flex items-center space-x-1.5 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={lowStockOnly}
                      onChange={(e) => setLowStockOnly(e.target.checked)}
                      className="rounded text-emerald-600 focus:ring-emerald-500"
                    />
                    <span className="text-slate-700 font-medium">Chỉ sản phẩm dưới định mức (Low stock)</span>
                  </label>
                  <label className="flex items-center space-x-1.5 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={expiringOnly}
                      onChange={(e) => setExpiringOnly(e.target.checked)}
                      className="rounded text-emerald-600 focus:ring-emerald-500"
                    />
                    <span className="text-slate-700 font-medium">Có lô sắp hết hạn</span>
                  </label>
                </div>
              </div>

              {/* Table */}
              {loadingProducts ? (
                <div className="space-y-2">
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                </div>
              ) : products.length === 0 ? (
                <EmptyState
                  title="Không tìm thấy sản phẩm"
                  description="Không có sản phẩm nào phù hợp với bộ lọc hiện tại."
                />
              ) : (
                <div className="bg-white border border-slate-200 rounded-lg overflow-x-auto shadow-2xs">
                  <table className="min-w-full text-xs text-left">
                    <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                      <tr>
                        <th className="px-4 py-3">Sản phẩm F&B</th>
                        <th className="px-3 py-3">Đơn vị</th>
                        <th className="px-3 py-3">Tồn khả dụng</th>
                        <th className="px-3 py-3">Định mức tối thiểu</th>
                        <th className="px-3 py-3">Số lô hoạt động</th>
                        <th className="px-3 py-3">Hạn dùng gần nhất</th>
                        <th className="px-3 py-3">Trạng thái tồn</th>
                        <th className="px-4 py-3 text-right">Thao tác</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {products.map((p) => (
                        <tr key={p.product_id} className="hover:bg-slate-50/80 transition">
                          <td className="px-4 py-3">
                            <span className="font-semibold text-slate-900 block">{p.product_name}</span>
                            <span className="text-[11px] font-mono text-slate-500">{p.sku}</span>
                          </td>
                          <td className="px-3 py-3 text-slate-600">{p.unit}</td>
                          <td className="px-3 py-3">
                            <span
                              className={`font-bold text-sm ${
                                p.is_low_stock ? 'text-amber-600' : 'text-emerald-700'
                              }`}
                            >
                              {p.total_available}
                            </span>
                          </td>
                          <td className="px-3 py-3 text-slate-600 font-mono">
                            {p.low_stock_threshold} {p.unit}
                          </td>
                          <td className="px-3 py-3 text-slate-700 font-medium">
                            {p.batch_count} lô
                          </td>
                          <td className="px-3 py-3">
                            {p.nearest_expiry ? (
                              <span
                                className={`${
                                  p.has_expired_batches
                                    ? 'text-rose-600 font-bold'
                                    : p.has_expiring_batches
                                    ? 'text-amber-600 font-semibold'
                                    : 'text-slate-600'
                                }`}
                              >
                                {new Date(p.nearest_expiry).toLocaleString('vi-VN')}
                              </span>
                            ) : (
                              <span className="text-slate-400">Chưa có lô</span>
                            )}
                          </td>
                          <td className="px-3 py-3">
                            {p.is_low_stock ? (
                              <Badge variant="warning">Thiếu hàng (Low)</Badge>
                            ) : (
                              <Badge variant="success">An toàn</Badge>
                            )}
                          </td>
                          <td className="px-4 py-3 text-right space-x-1.5 whitespace-nowrap">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openFefoForProduct(p.product_id)}
                            >
                              ⚡ Xuất FEFO
                            </Button>
                            {canWrite && (
                              <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => openReceiveForProduct(p.product_id)}
                              >
                                + Nhập lô
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: BATCHES LIST */}
          {activeTab === 'batches' && (
            <div className="space-y-4">
              {/* Filter Bar */}
              <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
                <div className="w-full sm:w-72">
                  <Input
                    type="text"
                    placeholder="Tìm theo mã lô hoặc tên..."
                    value={batchSearch}
                    onChange={(e) => setBatchSearch(e.target.value)}
                  />
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <select
                    value={batchStatusFilter}
                    onChange={(e) => setBatchStatusFilter(e.target.value)}
                    className="text-xs rounded-lg border border-slate-300 px-3 py-2 bg-white text-slate-800 focus:outline-none"
                  >
                    <option value="">Tất cả trạng thái</option>
                    <option value="ACTIVE">Đang hoạt động (ACTIVE)</option>
                    <option value="DEPLETED">Đã hết hàng (DEPLETED)</option>
                    <option value="EXPIRED">Hết hạn (EXPIRED)</option>
                    <option value="DISCARDED">Đã xuất hủy (DISCARDED)</option>
                  </select>

                  <select
                    value={batchExpiryDays}
                    onChange={(e) => setBatchExpiryDays(e.target.value)}
                    className="text-xs rounded-lg border border-slate-300 px-3 py-2 bg-white text-slate-800 focus:outline-none"
                  >
                    <option value="">Tất cả thời hạn</option>
                    <option value="1">Hết hạn trong 24 giờ</option>
                    <option value="3">Hết hạn trong 3 ngày</option>
                    <option value="7">Hết hạn trong 7 ngày</option>
                  </select>
                </div>
              </div>

              {/* Batches Table */}
              {loadingBatches ? (
                <div className="space-y-2">
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                </div>
              ) : batches.length === 0 ? (
                <EmptyState
                  title="Chưa có lô hàng nào"
                  description="Hãy thêm lô hàng mới để bắt đầu theo dõi tồn kho theo phương pháp FEFO."
                />
              ) : (
                <div className="bg-white border border-slate-200 rounded-lg overflow-x-auto shadow-2xs">
                  <table className="min-w-full text-xs text-left">
                    <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                      <tr>
                        <th className="px-4 py-3">Mã lô hàng</th>
                        <th className="px-3 py-3">Sản phẩm F&B</th>
                        <th className="px-3 py-3">Tồn / Nhập ban đầu</th>
                        <th className="px-3 py-3">Hạn sử dụng</th>
                        <th className="px-3 py-3">Thời gian còn lại</th>
                        <th className="px-3 py-3">Đơn giá vốn</th>
                        <th className="px-3 py-3">Nhà cung cấp</th>
                        <th className="px-3 py-3">Trạng thái</th>
                        <th className="px-4 py-3 text-right">Hành động</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {batches.map((b) => (
                        <tr key={b.id} className="hover:bg-slate-50/80 transition">
                          <td className="px-4 py-3">
                            <span className="font-mono font-bold text-slate-900 block">{b.batch_code}</span>
                            <span className="text-[11px] text-slate-400">
                              Nhập: {new Date(b.received_at).toLocaleDateString('vi-VN')}
                            </span>
                          </td>
                          <td className="px-3 py-3">
                            <span className="font-semibold text-slate-800 block">{b.product_name}</span>
                            <span className="text-[11px] font-mono text-slate-500">{b.product_sku}</span>
                          </td>
                          <td className="px-3 py-3">
                            <span className="font-bold text-slate-900">{b.quantity_available}</span>
                            <span className="text-slate-400"> / {b.quantity_received} {b.product_unit}</span>
                          </td>
                          <td className="px-3 py-3 font-medium">
                            {new Date(b.expiry_at).toLocaleString('vi-VN')}
                          </td>
                          <td className="px-3 py-3">
                            {b.is_expired ? (
                              <Badge variant="danger">Đã quá hạn</Badge>
                            ) : b.is_critical ? (
                              <Badge variant="danger">🚨 &lt; 24h ({b.hours_to_expiry}h)</Badge>
                            ) : b.is_warning ? (
                              <Badge variant="warning">⏳ {b.days_to_expiry} ngày</Badge>
                            ) : (
                              <span className="text-emerald-700 font-medium">
                                ✓ {b.days_to_expiry} ngày
                              </span>
                            )}
                          </td>
                          <td className="px-3 py-3 text-slate-700 font-mono">
                            {b.cost_per_unit ? `${b.cost_per_unit.toLocaleString('vi-VN')} đ` : '-'}
                          </td>
                          <td className="px-3 py-3 text-slate-600">
                            {b.supplier || <span className="text-slate-400">-</span>}
                          </td>
                          <td className="px-3 py-3">
                            <Badge
                              variant={
                                b.status === 'ACTIVE'
                                  ? 'success'
                                  : b.status === 'DEPLETED'
                                  ? 'neutral'
                                  : 'danger'
                              }
                            >
                              {b.status}
                            </Badge>
                          </td>
                          <td className="px-4 py-3 text-right">
                            {canWrite && b.status === 'ACTIVE' && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setAdjustBatch(b)}
                              >
                                ⚖️ Điều chỉnh / Hủy
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: EXPIRY ALERTS & WASTE RISK */}
          {activeTab === 'alerts' && (
            <div className="space-y-4">
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-900 flex items-start space-x-2">
                <span className="text-base">💡</span>
                <div>
                  <strong className="block font-semibold">Cơ chế Hạn dùng & Chống lãng phí (F&B Waste Prevention)</strong>
                  Danh sách này ưu tiên các lô hàng cận date cần xử lý gấp. Bạn có thể xuất hủy các lô đã hỏng hoặc chủ động kích hoạt chiến dịch <strong>AI Clear Stock / Flash Sale</strong> để bán hòa vốn trước khi hết hạn!
                </div>
              </div>

              {loadingAlerts ? (
                <div className="space-y-2">
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                </div>
              ) : alerts.length === 0 ? (
                <EmptyState
                  title="Không có cảnh báo rủi ro hạn dùng"
                  description="Tuyệt vời! Hiện tại không có lô hàng nào quá hạn hoặc sắp hết hạn trong 7 ngày tới."
                />
              ) : (
                <div className="bg-white border border-slate-200 rounded-lg overflow-x-auto shadow-2xs">
                  <table className="min-w-full text-xs text-left">
                    <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                      <tr>
                        <th className="px-4 py-3">Mức độ khẩn cấp</th>
                        <th className="px-3 py-3">Mã lô & Sản phẩm</th>
                        <th className="px-3 py-3">Tồn khả dụng</th>
                        <th className="px-3 py-3">Thời gian còn lại</th>
                        <th className="px-3 py-3">Hạn sử dụng</th>
                        <th className="px-3 py-3">Ước tính giá trị rủi ro</th>
                        <th className="px-3 py-3">Khuyến nghị hành động</th>
                        <th className="px-4 py-3 text-right">Thao tác</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {alerts.map((a) => (
                        <tr key={a.batch_id} className="hover:bg-slate-50/80 transition">
                          <td className="px-4 py-3">
                            {a.urgency === 'EXPIRED' && (
                              <Badge variant="danger">🔴 ĐÃ QUÁ HẠN</Badge>
                            )}
                            {a.urgency === 'CRITICAL' && (
                              <Badge variant="danger">⚡ KHẨN CẤP (&lt;24H)</Badge>
                            )}
                            {a.urgency === 'WARNING' && (
                              <Badge variant="warning">⏳ CẢNH BÁO (&lt;3 NGÀY)</Badge>
                            )}
                            {a.urgency === 'ATTENTION' && (
                              <Badge variant="neutral">👀 CHÚ Ý (&lt;7 NGÀY)</Badge>
                            )}
                          </td>
                          <td className="px-3 py-3">
                            <span className="font-semibold text-slate-900 block">{a.product_name}</span>
                            <span className="font-mono text-[11px] text-slate-500">{a.batch_code}</span>
                          </td>
                          <td className="px-3 py-3 font-bold text-slate-900 text-sm">
                            {a.quantity_available} phần
                          </td>
                          <td className="px-3 py-3 font-medium">
                            {a.urgency === 'EXPIRED' ? (
                              <span className="text-rose-600 font-bold">Đã quá hạn</span>
                            ) : (
                              <span className={a.hours_to_expiry <= 24 ? 'text-rose-600 font-bold' : 'text-amber-700 font-semibold'}>
                                {a.hours_to_expiry} giờ ({a.days_to_expiry} ngày)
                              </span>
                            )}
                          </td>
                          <td className="px-3 py-3 text-slate-600">
                            {new Date(a.expiry_at).toLocaleString('vi-VN')}
                          </td>
                          <td className="px-3 py-3 font-mono font-bold text-rose-700">
                            {a.estimated_waste_cost.toLocaleString('vi-VN')} đ
                          </td>
                          <td className="px-3 py-3">
                            {a.urgency === 'EXPIRED' ? (
                              <span className="text-rose-700 font-medium">Xuất hủy hỏng (WASTE_OUT)</span>
                            ) : a.urgency === 'CRITICAL' ? (
                              <span className="text-amber-700 font-medium">Flash Sale giảm 30-50% giải cứu</span>
                            ) : a.urgency === 'WARNING' ? (
                              <span className="text-slate-700">Tặng kèm combo đơn hàng</span>
                            ) : (
                              <span className="text-slate-500">Ưu tiên xuất trước (FEFO)</span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-right space-x-1.5 whitespace-nowrap">
                            {canWrite && (
                              <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => {
                                  // Fetch batch object or construct
                                  inventoryApi.getBatch(a.batch_id).then((b) => setAdjustBatch(b));
                                }}
                              >
                                {a.urgency === 'EXPIRED' ? 'Xuất hủy' : 'Điều chỉnh'}
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: INVENTORY MOVEMENTS LEDGER */}
          {activeTab === 'ledger' && (
            <div className="space-y-4">
              {/* Filter Bar */}
              <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
                <div className="flex items-center space-x-2 text-xs">
                  <span className="font-semibold text-slate-700">Lọc loại biến động:</span>
                  <select
                    value={movementTypeFilter}
                    onChange={(e) => setMovementTypeFilter(e.target.value)}
                    className="text-xs rounded-lg border border-slate-300 px-3 py-1.5 bg-white text-slate-800 focus:outline-none"
                  >
                    <option value="">Tất cả loại giao dịch</option>
                    <option value="PURCHASE_IN">Nhập kho theo lô (PURCHASE_IN)</option>
                    <option value="SALE_OUT">Xuất bán FEFO (SALE_OUT)</option>
                    <option value="WASTE_OUT">Xuất hủy hỏng/Hết hạn (WASTE_OUT)</option>
                    <option value="ADJUSTMENT_IN">Điều chỉnh tăng (ADJUSTMENT_IN)</option>
                    <option value="ADJUSTMENT_OUT">Điều chỉnh giảm (ADJUSTMENT_OUT)</option>
                    <option value="RETURN_IN">Nhập hoàn trả (RETURN_IN)</option>
                  </select>
                </div>
              </div>

              {/* Ledger Table */}
              {loadingMovements ? (
                <div className="space-y-2">
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                </div>
              ) : movements.length === 0 ? (
                <EmptyState
                  title="Chưa có dữ liệu sổ cái"
                  description="Mọi biến động nhập, xuất và điều chỉnh kho sẽ được ghi nhận tại đây."
                />
              ) : (
                <div className="bg-white border border-slate-200 rounded-lg overflow-x-auto shadow-2xs">
                  <table className="min-w-full text-xs text-left">
                    <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                      <tr>
                        <th className="px-4 py-3">Thời gian</th>
                        <th className="px-3 py-3">Loại biến động</th>
                        <th className="px-3 py-3">Mã lô</th>
                        <th className="px-3 py-3">Sản phẩm</th>
                        <th className="px-3 py-3">Số lượng</th>
                        <th className="px-3 py-3">Số dư (Trước → Sau)</th>
                        <th className="px-3 py-3">Lý do / Ghi chú</th>
                        <th className="px-3 py-3">Mã tham chiếu</th>
                        <th className="px-4 py-3">Người thực hiện</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {movements.map((m) => {
                        const isIncrease =
                          m.movement_type === 'PURCHASE_IN' ||
                          m.movement_type === 'ADJUSTMENT_IN' ||
                          m.movement_type === 'RETURN_IN';
                        return (
                          <tr key={m.id} className="hover:bg-slate-50/80 transition">
                            <td className="px-4 py-3 whitespace-nowrap text-slate-500">
                              {new Date(m.created_at).toLocaleString('vi-VN')}
                            </td>
                            <td className="px-3 py-3">
                              {m.movement_type === 'PURCHASE_IN' && (
                                <Badge variant="success">Nhập kho (IN)</Badge>
                              )}
                              {m.movement_type === 'SALE_OUT' && (
                                <Badge variant="neutral">Xuất bán (SALE)</Badge>
                              )}
                              {m.movement_type === 'WASTE_OUT' && (
                                <Badge variant="danger">Xuất hủy (WASTE)</Badge>
                              )}
                              {m.movement_type === 'ADJUSTMENT_IN' && (
                                <Badge variant="success">Tăng kiểm kê (+)</Badge>
                              )}
                              {m.movement_type === 'ADJUSTMENT_OUT' && (
                                <Badge variant="warning">Giảm kiểm kê (-)</Badge>
                              )}
                              {m.movement_type === 'RETURN_IN' && (
                                <Badge variant="success">Hoàn trả (RETURN)</Badge>
                              )}
                            </td>
                            <td className="px-3 py-3 font-mono font-semibold text-slate-800">
                              {m.batch_code}
                            </td>
                            <td className="px-3 py-3 font-medium text-slate-900">
                              {m.product_name}
                            </td>
                            <td className="px-3 py-3 font-bold font-mono">
                              <span className={isIncrease ? 'text-emerald-700' : 'text-rose-700'}>
                                {isIncrease ? `+${m.quantity}` : `-${m.quantity}`}
                              </span>
                            </td>
                            <td className="px-3 py-3 font-mono text-slate-600">
                              {m.previous_quantity} → {m.new_quantity}
                            </td>
                            <td className="px-3 py-3 text-slate-700">
                              {m.reason}
                              {m.note && <span className="block text-[11px] text-slate-400">{m.note}</span>}
                            </td>
                            <td className="px-3 py-3 font-mono text-[11px] text-slate-500">
                              {m.reference_id || '-'}
                            </td>
                            <td className="px-4 py-3 text-slate-600">
                              {m.created_by_user_name || <span className="text-slate-400">Hệ thống</span>}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Modals */}
          <ReceiveBatchModal
            isOpen={isReceiveModalOpen}
            onClose={() => setIsReceiveModalOpen(false)}
            onSuccess={refreshCurrentTab}
            initialProductId={receiveInitialProdId}
          />

          <AdjustStockModal
            isOpen={!!adjustBatch}
            onClose={() => setAdjustBatch(null)}
            onSuccess={refreshCurrentTab}
            batch={adjustBatch}
          />

          <FefoSimulatorModal
            isOpen={isFefoModalOpen}
            onClose={() => setIsFefoModalOpen(false)}
            onSuccess={refreshCurrentTab}
            initialProductId={fefoInitialProdId}
          />
        </div>
      </AdminShell>
    </ProtectedRoute>
  );
}
