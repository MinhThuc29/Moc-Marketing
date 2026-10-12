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
  CampaignListItem,
  CampaignOverviewStats,
  CampaignDetailResponse,
} from '@moc-healthy/contracts';
import { AdminShell } from '../../components/shell/AdminShell';
import { PageHeader } from '../../components/shell/PageHeader';
import { useAuth } from '../../context/AuthContext';
import { campaignsApi } from '../../lib/api';
import { CampaignDetailDrawer } from '../../components/marketing/CampaignDetailDrawer';
import { CampaignFormModal } from '../../components/marketing/CampaignFormModal';

const formatVND = (amount: number) => {
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
    maximumFractionDigits: 0,
  }).format(amount);
};

const formatDateRange = (start: string, end: string) => {
  try {
    const s = new Date(start).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' });
    const e = new Date(end).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
    return `${s} - ${e}`;
  } catch {
    return `${start} - ${end}`;
  }
};

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'ACTIVE':
      return <Badge variant="success">🟢 Đang chạy</Badge>;
    case 'READY_FOR_REVIEW':
      return <Badge variant="warning">⏳ Chờ duyệt</Badge>;
    case 'APPROVED':
      return <Badge variant="info">✅ Đã duyệt</Badge>;
    case 'DRAFT':
      return <Badge variant="neutral">📝 Bản nháp</Badge>;
    case 'PAUSED':
      return <Badge variant="warning">⏸️ Tạm dừng</Badge>;
    case 'COMPLETED':
      return <Badge variant="success">🏁 Hoàn tất</Badge>;
    case 'CANCELLED':
      return <Badge variant="danger">❌ Đã hủy</Badge>;
    default:
      return <Badge variant="neutral">{status}</Badge>;
  }
};

const getObjectiveBadge = (objective: string) => {
  switch (objective) {
    case 'CONVERSION':
      return <span className="text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 text-xs">🎯 Chuyển đổi</span>;
    case 'AWARENESS':
      return <span className="text-blue-700 font-semibold bg-blue-50 px-2 py-0.5 rounded border border-blue-200 text-xs">📢 Nhận diện</span>;
    case 'CLEARANCE':
      return <span className="text-amber-700 font-semibold bg-amber-50 px-2 py-0.5 rounded border border-amber-200 text-xs">⚡ Xả kho</span>;
    case 'LOYALTY':
      return <span className="text-purple-700 font-semibold bg-purple-50 px-2 py-0.5 rounded border border-purple-200 text-xs">👑 Tri ân</span>;
    case 'REENGAGEMENT':
      return <span className="text-slate-700 font-semibold bg-slate-100 px-2 py-0.5 rounded border border-slate-300 text-xs">🔄 Kích hoạt lại</span>;
    default:
      return <span className="text-xs text-slate-600">{objective}</span>;
  }
};

const STATUS_TABS = [
  { key: '', label: 'Tất cả' },
  { key: 'ACTIVE', label: '🟢 Đang chạy' },
  { key: 'READY_FOR_REVIEW', label: '⏳ Chờ duyệt' },
  { key: 'APPROVED', label: '✅ Đã duyệt' },
  { key: 'DRAFT', label: '📝 Bản nháp' },
  { key: 'COMPLETED', label: '🏁 Đã hoàn tất' },
];

export default function MarketingPage() {
  const { hasPermission } = useAuth();
  const canCreate = hasPermission('campaign.create');

  // Stats
  const [stats, setStats] = useState<CampaignOverviewStats | null>(null);
  const [isStatsLoading, setIsStatsLoading] = useState(true);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [objectiveFilter, setObjectiveFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 10;

  // List data
  const [campaigns, setCampaigns] = useState<CampaignListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  // Drawer & Modal state
  const [selectedCampaignId, setSelectedCampaignId] = useState<string | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [editingCampaign, setEditingCampaign] = useState<CampaignDetailResponse | null>(null);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
      setPage(1);
    }, 400);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  const loadStats = useCallback(async () => {
    setIsStatsLoading(true);
    try {
      const data = await campaignsApi.getOverview();
      setStats(data);
    } catch {
      // Fallback
    } finally {
      setIsStatsLoading(false);
    }
  }, []);

  const loadCampaigns = useCallback(async () => {
    setIsLoading(true);
    setFetchError(null);
    try {
      const res = await campaignsApi.list({
        status: statusFilter || undefined,
        objective: objectiveFilter || undefined,
        search: debouncedSearch.trim() || undefined,
        page,
        page_size: pageSize,
      });
      setCampaigns(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err: any) {
      setFetchError(err.message || 'Không thể tải danh sách chiến dịch');
    } finally {
      setIsLoading(false);
    }
  }, [statusFilter, objectiveFilter, debouncedSearch, page]);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  useEffect(() => {
    loadCampaigns();
  }, [loadCampaigns]);

  const handleOpenDetail = (id: string) => {
    setSelectedCampaignId(id);
    setIsDrawerOpen(true);
  };

  const handleCreateNew = () => {
    setEditingCampaign(null);
    setIsFormModalOpen(true);
  };

  const handleEdit = (camp: CampaignDetailResponse) => {
    setIsDrawerOpen(false);
    setEditingCampaign(camp);
    setIsFormModalOpen(true);
  };

  const handleDeleteDraft = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Bạn có chắc chắn muốn xóa bản nháp chiến dịch này?')) return;
    try {
      await campaignsApi.delete(id);
      loadCampaigns();
      loadStats();
    } catch (err: any) {
      alert(err.message || 'Không thể xóa chiến dịch');
    }
  };

  const columns: Column<CampaignListItem>[] = [
    {
      key: 'campaign',
      header: 'Chiến dịch',
      render: (item) => (
        <div className="flex flex-col">
          <span className="font-semibold text-slate-900 group-hover:text-emerald-700 transition-colors">
            {item.name}
          </span>
          <div className="flex items-center gap-1.5 mt-0.5">
            <span className="font-mono text-[11px] text-slate-500 bg-slate-100 px-1.5 py-0.2 rounded font-medium">
              {item.code}
            </span>
            <span className="text-[11px] text-slate-400">
              ({item.channels_count} kênh | {item.products_count} SP)
            </span>
          </div>
        </div>
      ),
    },
    {
      key: 'objective',
      header: 'Mục tiêu',
      render: (item) => getObjectiveBadge(item.objective),
    },
    {
      key: 'status',
      header: 'Trạng thái',
      render: (item) => getStatusBadge(item.status),
    },
    {
      key: 'timeline',
      header: 'Thời gian',
      render: (item) => (
        <span className="text-xs text-slate-700 font-medium">
          {formatDateRange(item.start_at, item.end_at)}
        </span>
      ),
    },
    {
      key: 'budget',
      header: 'Ngân sách / Đã chi',
      render: (item) => (
        <div className="flex flex-col text-xs">
          <span className="font-semibold text-slate-900">{formatVND(item.budget)}</span>
          <span className="text-slate-500 text-[11px]">Đã chi: {formatVND(item.actual_spend)}</span>
        </div>
      ),
    },
    {
      key: 'performance',
      header: 'Doanh thu / ROI',
      render: (item) => (
        <div className="flex flex-col text-xs">
          <span className="font-semibold text-emerald-700">{formatVND(item.revenue_attributed)}</span>
          <span
            className={`font-bold text-[11px] ${
              item.roi_percentage > 0
                ? 'text-emerald-600'
                : item.roi_percentage < 0
                ? 'text-rose-600'
                : 'text-slate-400'
            }`}
          >
            ROI: {item.roi_percentage > 0 ? `+${item.roi_percentage}%` : `${item.roi_percentage}%`}
          </span>
        </div>
      ),
    },
    {
      key: 'actions',
      header: 'Thao tác',
      render: (item) => (
        <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleOpenDetail(item.id)}
            className="text-xs py-1 px-2.5"
          >
            Chi tiết
          </Button>
          {item.status === 'DRAFT' && canCreate && (
            <Button
              variant="danger"
              size="sm"
              onClick={(e) => handleDeleteDraft(item.id, e)}
              className="text-xs py-1 px-2"
              title="Xóa bản nháp"
            >
              🗑️
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <AdminShell requiredPermission="campaign.create">
      <div className="space-y-6">
        <PageHeader
          title="Không gian Tiếp thị (Marketing Campaigns)"
          subtitle="Điều phối chiến dịch đa kênh, tối ưu hạn mức ngân sách, theo dõi phân bổ doanh thu & tỷ lệ ROI"
          breadcrumbs={[{ label: 'Marketing Hub' }]}
          actions={
            canCreate ? (
              <Button variant="primary" size="sm" onClick={handleCreateNew}>
                + Thiết lập chiến dịch mới
              </Button>
            ) : undefined
          }
        />

        {/* Overview Stats */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <StatCard
            title="Đang hoạt động"
            value={stats ? `${stats.active_campaigns} chiến dịch` : '---'}
            period="Chiến dịch đang phân phối"
          />
          <StatCard
            title="Chờ phê duyệt"
            value={stats ? `${stats.ready_for_review_campaigns}` : '---'}
            period="Kế hoạch đang đợi duyệt"
          />
          <StatCard
            title="Ngân sách đã duyệt"
            value={stats ? formatVND(stats.total_budget_approved) : '---'}
            period="Hạn mức đầu tư tiếp thị"
          />
          <StatCard
            title="Doanh thu ghi nhận"
            value={stats ? formatVND(stats.total_revenue_attributed) : '---'}
            period="Doanh số phân bổ campaign"
          />
          <StatCard
            title="ROI Trung bình"
            value={stats ? `${stats.average_roi_percentage}%` : '---'}
            period="Tỷ suất sinh lời tiếp thị"
          />
        </div>

        {/* Filters & Status Tabs */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-4 shadow-xs">
          {/* Tabs */}
          <div className="flex border-b border-slate-200 overflow-x-auto pb-1 gap-1">
            {STATUS_TABS.map((tab) => {
              const isActive = statusFilter === tab.key;
              return (
                <button
                  key={tab.key}
                  type="button"
                  onClick={() => {
                    setStatusFilter(tab.key);
                    setPage(1);
                  }}
                  className={`px-3.5 py-2 text-xs font-medium rounded-t-lg transition-colors whitespace-nowrap border-b-2 -mb-[5px] ${
                    isActive
                      ? 'border-emerald-600 text-emerald-800 bg-emerald-50/50 font-bold'
                      : 'border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Search & Objective Dropdown */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="sm:col-span-2">
              <Input
                placeholder="🔍 Tìm kiếm chiến dịch theo tên, mã (vd: CAMP-AUTUMN), ghi chú..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <div>
              <Select
                value={objectiveFilter}
                onChange={(e) => {
                  setObjectiveFilter(e.target.value);
                  setPage(1);
                }}
                options={[
                  { value: '', label: 'Tất cả mục tiêu' },
                  { value: 'CONVERSION', label: '🎯 Tăng chuyển đổi' },
                  { value: 'AWARENESS', label: '📢 Nhận diện thương hiệu' },
                  { value: 'CLEARANCE', label: '⚡ Xả kho cận date' },
                  { value: 'LOYALTY', label: '👑 Tri ân khách hàng' },
                  { value: 'REENGAGEMENT', label: '🔄 Kích hoạt lại' },
                ]}
              />
            </div>
          </div>
        </div>

        {/* Campaign List Table */}
        {fetchError ? (
          <ErrorState
            title="Lỗi tải dữ liệu chiến dịch"
            message={fetchError}
            onRetry={loadCampaigns}
          />
        ) : campaigns.length === 0 && !isLoading ? (
          <EmptyState
            title="Chưa tìm thấy chiến dịch nào"
            description={
              searchTerm || statusFilter || objectiveFilter
                ? 'Không có chiến dịch nào khớp với điều kiện lọc hiện tại.'
                : 'Bắt đầu bằng cách tạo kế hoạch chiến dịch tiếp thị mới.'
            }
            icon="🎯"
            actionText={canCreate ? '+ Tạo chiến dịch đầu tiên' : undefined}
            onAction={canCreate ? handleCreateNew : undefined}
          />
        ) : (
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
            <DataTable<CampaignListItem>
              columns={columns}
              data={campaigns}
              keyExtractor={(item: CampaignListItem) => item.id}
              isLoading={isLoading}
              currentPage={page}
              totalPages={totalPages}
              onPageChange={(p: number) => setPage(p)}
            />
          </div>
        )}

        {/* Drawer Detail */}
        <CampaignDetailDrawer
          isOpen={isDrawerOpen}
          onClose={() => setIsDrawerOpen(false)}
          campaignId={selectedCampaignId}
          onCampaignUpdated={() => {
            loadCampaigns();
            loadStats();
          }}
          onEdit={handleEdit}
        />

        {/* Create/Edit Modal */}
        <CampaignFormModal
          isOpen={isFormModalOpen}
          onClose={() => {
            setIsFormModalOpen(false);
            setEditingCampaign(null);
          }}
          campaign={editingCampaign}
          onSuccess={() => {
            loadCampaigns();
            loadStats();
          }}
        />
      </div>
    </AdminShell>
  );
}
