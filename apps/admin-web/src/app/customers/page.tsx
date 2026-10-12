'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Button,
  Input,
  Select,
  Badge,
  DataTable,
  Column,
  EmptyState,
  ErrorState,
  StatCard,
} from '@moc-healthy/ui';
import {
  CustomerListItem,
  CustomerOverviewStats,
  CustomerSegment,
} from '@moc-healthy/contracts';
import { AdminShell } from '../../components/shell/AdminShell';
import { PageHeader } from '../../components/shell/PageHeader';
import { useAuth } from '../../context/AuthContext';
import { customersApi } from '../../lib/api';
import { Customer360Drawer } from '../../components/customers/Customer360Drawer';
import { CustomerFormModal } from '../../components/customers/CustomerFormModal';

const formatVND = (amount: number) => {
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
    maximumFractionDigits: 0,
  }).format(amount);
};

const getSegmentBadge = (segment: string) => {
  switch (segment) {
    case 'VIP':
      return <Badge variant="warning">👑 VIP</Badge>;
    case 'REPEAT':
      return <Badge variant="success">🔄 Quay lại</Badge>;
    case 'ACTIVE':
      return <Badge variant="info">🟢 Đang mua</Badge>;
    case 'NEW':
      return <Badge variant="neutral">✨ Khách mới</Badge>;
    case 'AT_RISK':
      return <Badge variant="danger">⚠️ Có nguy cơ</Badge>;
    case 'DORMANT':
      return <Badge variant="neutral">💤 Ngủ đông</Badge>;
    case 'HIGH_VALUE':
      return <Badge variant="warning">💎 Giá trị cao</Badge>;
    default:
      return <Badge variant="neutral">{segment}</Badge>;
  }
};

export default function CustomersPage() {
  const { hasPermission } = useAuth();
  const canWrite = hasPermission('customer.write');

  // Stats
  const [stats, setStats] = useState<CustomerOverviewStats | null>(null);

  // List state
  const [customers, setCustomers] = useState<CustomerListItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  // Filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSegment, setSelectedSegment] = useState<string>('');
  const [sortBy, setSortBy] = useState('created_at_desc');

  // UI state
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Modal / Drawer state
  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(null);
  const [is360DrawerOpen, setIs360DrawerOpen] = useState(false);
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<CustomerListItem | null>(null);

  const loadStats = useCallback(async () => {
    try {
      const data = await customersApi.getOverview();
      setStats(data);
    } catch (err) {
      console.error('Không thể tải thống kê CRM:', err);
    }
  }, []);

  const loadCustomers = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const res = await customersApi.list({
        segment: selectedSegment || undefined,
        search: searchTerm.trim() || undefined,
        sort_by: sortBy,
        page: currentPage,
        page_size: pageSize,
      });
      setCustomers(res.items);
      setTotalCount(res.total);
      setTotalPages(res.total_pages);
    } catch (err: any) {
      setErrorMessage(err.message || 'Không thể tải danh sách khách hàng');
    } finally {
      setIsLoading(false);
    }
  }, [selectedSegment, searchTerm, sortBy, currentPage]);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  useEffect(() => {
    loadCustomers();
  }, [loadCustomers]);

  const handleRefresh = () => {
    loadStats();
    loadCustomers();
  };

  const handleOpen360 = (id: string) => {
    setSelectedCustomerId(id);
    setIs360DrawerOpen(true);
  };

  const handleOpenEdit = (customer: CustomerListItem) => {
    setEditingCustomer(customer);
    setIsFormModalOpen(true);
  };

  const handleOpenCreate = () => {
    setEditingCustomer(null);
    setIsFormModalOpen(true);
  };

  const segmentTabs = [
    { key: '', label: 'Tất cả khách hàng' },
    { key: 'VIP', label: '👑 Khách VIP' },
    { key: 'ACTIVE', label: '🟢 Đang mua' },
    { key: 'REPEAT', label: '🔄 Quay lại' },
    { key: 'NEW', label: '✨ Khách mới' },
    { key: 'AT_RISK', label: '⚠️ Có nguy cơ' },
    { key: 'DORMANT', label: '💤 Ngủ đông' },
  ];

  const columns: Column<CustomerListItem>[] = [
    {
      key: 'name',
      header: 'Khách hàng',
      render: (item: CustomerListItem) => (
        <div className="space-y-0.5">
          <button
            type="button"
            onClick={() => handleOpen360(item.id)}
            className="font-bold text-slate-900 text-xs hover:text-emerald-700 text-left block"
          >
            {item.full_name}
          </button>
          <a
            href={`tel:${item.phone}`}
            className="text-[11px] text-emerald-700 hover:underline font-mono block"
            onClick={(e) => e.stopPropagation()}
          >
            📞 {item.phone}
          </a>
          {item.email && (
            <span className="text-[10px] text-slate-400 block truncate max-w-[160px]">
              {item.email}
            </span>
          )}
        </div>
      ),
    },
    {
      key: 'segment',
      header: 'Phân khúc RFM',
      render: (item: CustomerListItem) => (
        <div className="space-y-1">
          {getSegmentBadge(item.segment)}
          <span className="text-[10px] text-slate-400 block">Nguồn: {item.source}</span>
        </div>
      ),
    },
    {
      key: 'orders_spent',
      header: 'Đơn hàng & Chi tiêu',
      render: (item: CustomerListItem) => (
        <div className="space-y-0.5">
          <span className="font-extrabold text-slate-900 text-xs block">
            {formatVND(item.total_spent)}
          </span>
          <span className="text-[11px] text-slate-500 block font-mono">
            {item.order_count} đơn hàng
          </span>
          <span className="text-[10px] text-slate-400 block">
            AOV: {formatVND(item.average_order_value)}
          </span>
        </div>
      ),
    },
    {
      key: 'loyalty',
      header: 'Điểm Mộc Xu',
      render: (item: CustomerListItem) => (
        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-amber-50 border border-amber-200">
          <span className="text-xs">🪙</span>
          <span className="font-bold text-amber-900 text-xs font-mono">
            {item.loyalty_points.toLocaleString('vi-VN')}
          </span>
        </div>
      ),
    },
    {
      key: 'last_order',
      header: 'Lần mua gần nhất',
      render: (item: CustomerListItem) => (
        <div className="space-y-0.5 text-xs text-slate-600">
          <span>
            {item.last_order_at
              ? new Date(item.last_order_at).toLocaleDateString('vi-VN')
              : 'Chưa có'}
          </span>
          {item.tags && item.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {item.tags.slice(0, 2).map((t, idx) => (
                <span key={idx} className="text-[9px] bg-slate-100 text-slate-600 px-1.5 py-0.2 rounded">
                  #{t}
                </span>
              ))}
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'actions',
      header: 'Thao tác',
      render: (item: CustomerListItem) => (
        <div className="flex items-center gap-1.5">
          <Button
            variant="outline"
            size="sm"
            className="text-xs"
            onClick={() => handleOpen360(item.id)}
          >
            👁️ Xem 360°
          </Button>
          {canWrite && (
            <Button
              variant="outline"
              size="sm"
              className="text-xs text-slate-600"
              onClick={() => handleOpenEdit(item)}
            >
              ✏️
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <AdminShell requiredPermission="customer.read">
      <PageHeader
        title="Quản lý Khách hàng & CRM (Customer 360)"
        subtitle="Hồ sơ khách hàng hợp nhất, phân nhóm RFM, tích điểm Mộc Xu và phân tích hành vi tiêu dùng"
        breadcrumbs={[{ label: 'Khách hàng' }]}
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isLoading}>
              🔄 Làm mới
            </Button>
            {canWrite && (
              <Button variant="primary" size="sm" onClick={handleOpenCreate}>
                + Thêm khách hàng
              </Button>
            )}
          </div>
        }
      />

      {/* 1. Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          title="Tổng khách hàng"
          value={stats ? stats.total_customers.toLocaleString('vi-VN') : '—'}
          period="Đã lưu trữ trong CRM"
          icon="👥"
        />
        <StatCard
          title="Khách hàng VIP"
          value={stats ? stats.vip_customers.toLocaleString('vi-VN') : '—'}
          period="Chi tiêu ≥ 2tr hoặc ≥ 8 đơn"
          icon="👑"
        />
        <StatCard
          title="Khách mới tháng này"
          value={stats ? stats.new_customers_this_month.toLocaleString('vi-VN') : '—'}
          period="Tăng trưởng cơ sở dữ liệu"
          icon="✨"
        />
        <StatCard
          title="Khách có nguy cơ rời bỏ"
          value={stats ? stats.at_risk_customers.toLocaleString('vi-VN') : '—'}
          period="> 30 ngày chưa đặt lại món"
          icon="⚠️"
        />
      </div>

      {/* 2. Filters & Segment Tabs */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-4 shadow-xs mb-6 space-y-4">
        {/* Segment Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs border-b border-slate-100">
          <span className="text-slate-400 font-medium mr-2 shrink-0">Phân khúc RFM:</span>
          {segmentTabs.map((tab) => {
            const isActive = selectedSegment === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => {
                  setSelectedSegment(tab.key);
                  setCurrentPage(1);
                }}
                className={`px-3 py-1.5 rounded-lg font-medium transition-all shrink-0 ${
                  isActive
                    ? 'bg-emerald-700 text-white shadow-xs'
                    : 'bg-slate-50 text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Detailed Search row */}
        <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-end">
          <div className="sm:col-span-8">
            <Input
              label="Tìm kiếm khách hàng"
              placeholder="Họ tên, số điện thoại (09xxx), hoặc địa chỉ email..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
            />
          </div>

          <div className="sm:col-span-4">
            <Select
              label="Sắp xếp theo"
              value={sortBy}
              onChange={(e) => {
                setSortBy(e.target.value);
                setCurrentPage(1);
              }}
              options={[
                { value: 'created_at_desc', label: 'Mới tạo gần nhất' },
                { value: 'total_spent_desc', label: 'Chi tiêu cao nhất (LTV)' },
                { value: 'order_count_desc', label: 'Số đơn nhiều nhất' },
                { value: 'last_order_desc', label: 'Đặt hàng gần nhất' },
              ]}
            />
          </div>
        </div>
      </div>

      {/* 3. Customers Table */}
      {errorMessage ? (
        <ErrorState
          title="Không thể tải danh sách khách hàng"
          message={errorMessage}
          onRetry={loadCustomers}
        />
      ) : customers.length === 0 && !isLoading ? (
        <EmptyState
          title="Không tìm thấy khách hàng nào"
          description={
            searchTerm || selectedSegment
              ? 'Thử thay đổi từ khóa tìm kiếm hoặc bỏ chọn bộ lọc phân khúc.'
              : 'Chưa có hồ sơ khách hàng nào trong hệ thống.'
          }
          icon="👥"
          actionText={
            searchTerm || selectedSegment
              ? 'Xóa bộ lọc'
              : canWrite
              ? '+ Thêm khách hàng đầu tiên'
              : undefined
          }
          onAction={
            searchTerm || selectedSegment
              ? () => {
                  setSearchTerm('');
                  setSelectedSegment('');
                  setCurrentPage(1);
                }
              : canWrite
              ? handleOpenCreate
              : undefined
          }
        />
      ) : (
        <DataTable
          columns={columns}
          data={customers}
          keyExtractor={(item) => item.id}
          isLoading={isLoading}
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={(page) => setCurrentPage(page)}
        />
      )}

      {/* 4. Customer 360 Drawer */}
      <Customer360Drawer
        isOpen={is360DrawerOpen}
        onClose={() => setIs360DrawerOpen(false)}
        customerId={selectedCustomerId}
        onCustomerUpdated={handleRefresh}
      />

      {/* 5. Customer Form Modal */}
      <CustomerFormModal
        isOpen={isFormModalOpen}
        onClose={() => setIsFormModalOpen(false)}
        customer={editingCustomer}
        onSuccess={handleRefresh}
      />
    </AdminShell>
  );
}
