'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  WorkflowListItem,
  WorkflowDetailResponse,
  AutomationOverviewStats,
  AutomationRunListItem,
  AutomationRunDetailResponse,
} from '@moc-healthy/contracts';
import { automationApi } from '../../lib/api';
import { AdminShell } from '../../components/shell/AdminShell';
import { PageHeader } from '../../components/shell/PageHeader';
import { Button, Badge } from '@moc-healthy/ui';
import { WorkflowDetailDrawer } from '../../components/automation/WorkflowDetailDrawer';
import { WorkflowFormModal } from '../../components/automation/WorkflowFormModal';
import { WorkflowTestRunModal } from '../../components/automation/WorkflowTestRunModal';

const TRIGGER_LABELS: Record<string, { label: string; icon: string; color: string }> = {
  CUSTOMER_CREATED: { label: 'Khách hàng mới', icon: '👤', color: 'bg-blue-50 text-blue-700' },
  CART_ABANDONED: { label: 'Giỏ hàng bỏ quên', icon: '🛒', color: 'bg-amber-50 text-amber-700' },
  ORDER_COMPLETED: { label: 'Đơn hàng hoàn tất', icon: '✅', color: 'bg-emerald-50 text-emerald-700' },
  CUSTOMER_INACTIVE: { label: 'Khách ngừng mua', icon: '💤', color: 'bg-purple-50 text-purple-700' },
  INVENTORY_EXPIRY_RISK: { label: 'Tồn kho cận date', icon: '⏰', color: 'bg-rose-50 text-rose-700' },
  LOW_STOCK: { label: 'Tồn kho thấp', icon: '📦', color: 'bg-orange-50 text-orange-700' },
  CAMPAIGN_ENDING: { label: 'Chiến dịch kết thúc', icon: '🏁', color: 'bg-indigo-50 text-indigo-700' },
};

const ACTION_LABELS: Record<string, { label: string; icon: string }> = {
  SEND_ZALO_MOCK: { label: 'Zalo OA', icon: '💬' },
  SEND_EMAIL_MOCK: { label: 'Email', icon: '✉️' },
  ISSUE_PROMOTION: { label: 'Voucher', icon: '🎟️' },
  ADD_LOYALTY_POINTS: { label: 'Mộc Xu', icon: '⭐' },
  ADD_CUSTOMER_TAG: { label: 'Tag', icon: '🏷️' },
  CREATE_NOTIFICATION: { label: 'Cảnh báo', icon: '🔔' },
  CREATE_RECOMMENDATION: { label: 'Đề xuất AI', icon: '💡' },
  CREATE_CAMPAIGN_DRAFT: { label: 'Draft Camp', icon: '📋' },
  WAIT_HOURS: { label: 'Chờ', icon: '⏳' },
};

export default function AutomationPage() {
  const [activeTab, setActiveTab] = useState<'workflows' | 'runs'>('workflows');
  const [stats, setStats] = useState<AutomationOverviewStats | null>(null);
  const [workflows, setWorkflows] = useState<WorkflowListItem[]>([]);
  const [runs, setRuns] = useState<AutomationRunListItem[]>([]);
  const [totalWorkflows, setTotalWorkflows] = useState(0);
  const [totalRuns, setTotalRuns] = useState(0);

  // Filters
  const [triggerFilter, setTriggerFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [search, setSearch] = useState('');
  const [runsStatusFilter, setRunsStatusFilter] = useState('ALL');

  // Loading states
  const [isLoading, setIsLoading] = useState(true);
  const [isRunsLoading, setIsRunsLoading] = useState(false);

  // Modals & Drawer State
  const [selectedWorkflowDetail, setSelectedWorkflowDetail] = useState<WorkflowDetailResponse | null>(null);
  const [isDetailDrawerOpen, setIsDetailDrawerOpen] = useState(false);

  const [formModalOpen, setFormModalOpen] = useState(false);
  const [editingWorkflow, setEditingWorkflow] = useState<WorkflowListItem | null>(null);

  const [testRunModalOpen, setTestRunModalOpen] = useState(false);
  const [testRunWorkflow, setTestRunWorkflow] = useState<WorkflowListItem | null>(null);

  const [selectedRunDetail, setSelectedRunDetail] = useState<AutomationRunDetailResponse | null>(null);
  const [isRunDetailModalOpen, setIsRunDetailModalOpen] = useState(false);

  // Fetch Overview Stats
  const fetchStats = useCallback(async () => {
    try {
      const s = await automationApi.getOverview();
      setStats(s);
    } catch (err) {
      console.error('Failed to fetch overview stats', err);
    }
  }, []);

  // Fetch Workflows
  const fetchWorkflows = useCallback(async () => {
    try {
      setIsLoading(true);
      const res = await automationApi.listWorkflows({
        trigger_type: triggerFilter !== 'ALL' ? triggerFilter : undefined,
        status: statusFilter !== 'ALL' ? statusFilter : undefined,
        search: search.trim() || undefined,
        limit: 50,
      });
      setWorkflows(res.items);
      setTotalWorkflows(res.total);
    } catch (err) {
      console.error('Failed to list workflows', err);
    } finally {
      setIsLoading(false);
    }
  }, [triggerFilter, statusFilter, search]);

  // Fetch Runs
  const fetchRuns = useCallback(async () => {
    try {
      setIsRunsLoading(true);
      const res = await automationApi.listRuns({
        status: runsStatusFilter !== 'ALL' ? runsStatusFilter : undefined,
        limit: 50,
      });
      setRuns(res.items);
      setTotalRuns(res.total);
    } catch (err) {
      console.error('Failed to list runs', err);
    } finally {
      setIsRunsLoading(false);
    }
  }, [runsStatusFilter]);

  useEffect(() => {
    fetchStats();
    fetchWorkflows();
  }, [fetchStats, fetchWorkflows]);

  useEffect(() => {
    if (activeTab === 'runs') {
      fetchRuns();
    }
  }, [activeTab, fetchRuns]);

  // Toggle status
  const handleToggleStatus = async (workflowId: string, currentStatus: string) => {
    const nextStatus = currentStatus === 'ACTIVE' ? 'PAUSED' : 'ACTIVE';
    try {
      await automationApi.toggleStatus(workflowId, nextStatus);
      await fetchWorkflows();
      await fetchStats();
      if (selectedWorkflowDetail && selectedWorkflowDetail.id === workflowId) {
        const updatedDetail = await automationApi.getWorkflow(workflowId);
        setSelectedWorkflowDetail(updatedDetail);
      }
    } catch (err: any) {
      alert(err.message || 'Lỗi khi đổi trạng thái');
    }
  };

  // Open Detail Drawer
  const handleOpenDetail = async (w: WorkflowListItem) => {
    try {
      const detail = await automationApi.getWorkflow(w.id);
      setSelectedWorkflowDetail(detail);
      setIsDetailDrawerOpen(true);
    } catch (err: any) {
      alert(err.message || 'Không thể tải chi tiết');
    }
  };

  // Delete Workflow
  const handleDelete = async (w: WorkflowListItem) => {
    if (!confirm(`Bạn có chắc chắn muốn xóa kịch bản "${w.name}"?`)) return;
    try {
      await automationApi.deleteWorkflow(w.id);
      await fetchWorkflows();
      await fetchStats();
    } catch (err: any) {
      alert(err.message || 'Không thể xóa kịch bản');
    }
  };

  // Open Run Detail
  const handleOpenRunDetail = async (runId: string) => {
    try {
      const detail = await automationApi.getRunDetail(runId);
      setSelectedRunDetail(detail);
      setIsRunDetailModalOpen(true);
    } catch (err: any) {
      alert(err.message || 'Không thể tải chi tiết lượt chạy');
    }
  };

  return (
    <AdminShell requiredPermission="settings.manage">
      <PageHeader
        title="Marketing Automation & Customer Journeys"
        subtitle="Tự động hóa hành trình khách hàng F&B: Chào đón khách mới, giỏ hàng bỏ quên, kích hoạt khách rời bỏ và cảnh báo xả kho"
        breadcrumbs={[{ label: 'Tự động hóa' }]}
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                const demoTrigger = prompt('Nhập Trigger Type (vd: CUSTOMER_CREATED, CART_ABANDONED):', 'CUSTOMER_CREATED');
                if (demoTrigger) {
                  automationApi.dispatchTrigger({
                    trigger_type: demoTrigger,
                    source_id: 'manual-pos-dispatch',
                    context: { customer_name: 'Khách hàng POS', customer_phone: '0988001122', consent_marketing: true, cart_total: 120000 },
                  }).then((res) => {
                    alert(res.summary);
                    fetchStats();
                    if (activeTab === 'runs') fetchRuns();
                  }).catch((e) => alert(e.message));
                }
              }}
            >
              ⚡ Dispatch Sự Kiện
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                setEditingWorkflow(null);
                setFormModalOpen(true);
              }}
            >
              + Tạo Kịch Bản Mới
            </Button>
          </div>
        }
      />

      {/* Top 4 Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Tổng kịch bản</p>
            <p className="text-2xl font-bold text-slate-800 mt-1">{stats?.total_workflows ?? '-'}</p>
            <p className="text-xs text-slate-500 mt-0.5">{stats?.active_templates_count ?? 0} mẫu hệ thống</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center text-xl font-bold">
            ⚡
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Đang hoạt động</p>
            <p className="text-2xl font-bold text-emerald-600 mt-1">{stats?.active_workflows ?? '-'}</p>
            <p className="text-xs text-slate-500 mt-0.5">{stats?.paused_workflows ?? 0} kịch bản tạm dừng</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center text-xl font-bold">
            🟢
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Tổng lượt thực thi</p>
            <p className="text-2xl font-bold text-slate-800 mt-1">{stats?.total_runs?.toLocaleString('vi-VN') ?? '-'}</p>
            <p className="text-xs text-slate-500 mt-0.5">Tự động hoàn toàn 24/7</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center text-xl font-bold">
            🔄
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Tỷ lệ thành công</p>
            <p className="text-2xl font-bold text-blue-600 mt-1">{stats ? `${stats.success_rate}%` : '-'}</p>
            <p className="text-xs text-emerald-600 font-medium mt-0.5">{stats?.successful_runs ?? 0} thành công / {stats?.failed_runs ?? 0} lỗi</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center text-xl font-bold">
            🎯
          </div>
        </div>
      </div>

      {/* Main Tabs Navigation */}
      <div className="border-b border-slate-200 mb-6 flex items-center justify-between">
        <div className="flex gap-8">
          <button
            onClick={() => setActiveTab('workflows')}
            className={`pb-3 text-sm font-semibold transition-colors relative ${
              activeTab === 'workflows'
                ? 'text-emerald-700 border-b-2 border-emerald-600 font-bold'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            📋 Kịch Bản Hành Trình ({totalWorkflows})
          </button>
          <button
            onClick={() => setActiveTab('runs')}
            className={`pb-3 text-sm font-semibold transition-colors relative ${
              activeTab === 'runs'
                ? 'text-emerald-700 border-b-2 border-emerald-600 font-bold'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            📜 Lịch Sử Thực Thi Logs ({totalRuns})
          </button>
        </div>
      </div>

      {/* TAB 1: WORKFLOWS */}
      {activeTab === 'workflows' && (
        <div className="space-y-4">
          {/* Filters Bar */}
          <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-sm flex flex-wrap items-center gap-3 justify-between">
            <div className="flex flex-wrap items-center gap-3 flex-1">
              <input
                type="text"
                placeholder="Tìm theo tên hoặc mã kịch bản..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="text-xs p-2.5 rounded-lg border border-slate-200 w-64 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />

              <select
                value={triggerFilter}
                onChange={(e) => setTriggerFilter(e.target.value)}
                className="text-xs p-2.5 rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value="ALL">Tất cả Trigger</option>
                <option value="CUSTOMER_CREATED">👤 Khách hàng mới</option>
                <option value="CART_ABANDONED">🛒 Giỏ hàng bỏ quên</option>
                <option value="ORDER_COMPLETED">✅ Đơn hoàn tất</option>
                <option value="CUSTOMER_INACTIVE">💤 Khách ngừng mua</option>
                <option value="INVENTORY_EXPIRY_RISK">⏰ Tồn cận date</option>
                <option value="LOW_STOCK">📦 Tồn kho thấp</option>
              </select>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="text-xs p-2.5 rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value="ALL">Tất cả Trạng thái</option>
                <option value="ACTIVE">🟢 Đang hoạt động</option>
                <option value="PAUSED">⏸️ Tạm dừng</option>
                <option value="DRAFT">📝 Bản nháp</option>
              </select>
            </div>
          </div>

          {/* Workflows Grid Cards */}
          {isLoading ? (
            <div className="p-12 text-center text-slate-400 text-sm">
              Đang tải danh sách kịch bản tự động hóa...
            </div>
          ) : workflows.length === 0 ? (
            <div className="p-12 text-center bg-white rounded-2xl border border-slate-200 text-slate-500 text-sm">
              Không tìm thấy kịch bản nào phù hợp với bộ lọc.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {workflows.map((wf) => {
                const triggerMeta = TRIGGER_LABELS[wf.trigger_type] || {
                  label: wf.trigger_type,
                  icon: '⚡',
                  color: 'bg-gray-100 text-gray-700',
                };
                const isActive = wf.status === 'ACTIVE';

                return (
                  <div
                    key={wf.id}
                    className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-5 flex flex-col justify-between hover:shadow-md transition-shadow relative"
                  >
                    <div>
                      {/* Top Badges */}
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${triggerMeta.color}`}>
                            <span>{triggerMeta.icon}</span>
                            <span>{triggerMeta.label}</span>
                          </span>
                          <span className="font-mono text-xs text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                            {wf.code}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          {wf.is_system_template && (
                            <span className="text-[11px] bg-emerald-50 text-emerald-800 font-semibold px-2 py-0.5 rounded border border-emerald-100">
                              Mẫu chuẩn
                            </span>
                          )}
                          <Badge variant={isActive ? 'success' : 'neutral'}>
                            {isActive ? 'ĐANG CHẠY' : wf.status}
                          </Badge>
                        </div>
                      </div>

                      {/* Title & Desc */}
                      <h3 className="text-base font-bold text-slate-800 mb-1">{wf.name}</h3>
                      {wf.description && (
                        <p className="text-xs text-slate-500 line-clamp-2 mb-3 leading-relaxed">
                          {wf.description}
                        </p>
                      )}

                      {/* Visual Condition & Actions summary */}
                      <div className="bg-slate-50/70 p-3 rounded-xl border border-slate-100 mb-4 space-y-2">
                        {/* Conditions */}
                        <div className="flex items-center gap-1.5 text-xs">
                          <span className="text-[11px] font-bold text-amber-700 uppercase">IF:</span>
                          {(!wf.conditions || wf.conditions.length === 0) ? (
                            <span className="text-[11px] text-slate-400 italic">Mọi sự kiện</span>
                          ) : (
                            <div className="flex flex-wrap gap-1">
                              {wf.conditions.map((c, i) => (
                                <span key={i} className="text-[11px] bg-white text-slate-700 px-1.5 py-0.5 rounded border border-amber-200 font-mono">
                                  {c.field} {c.operator} {String(c.value)}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>

                        {/* Actions Chain */}
                        <div className="flex items-center gap-1.5 text-xs">
                          <span className="text-[11px] font-bold text-emerald-700 uppercase">DO:</span>
                          <div className="flex flex-wrap items-center gap-1">
                            {wf.actions?.map((act, i) => {
                              const aMeta = ACTION_LABELS[act.type] || { label: act.type, icon: '⚙️' };
                              return (
                                <React.Fragment key={i}>
                                  <span className="text-[11px] bg-white text-slate-700 px-1.5 py-0.5 rounded border border-emerald-200 font-medium inline-flex items-center gap-1">
                                    <span>{aMeta.icon}</span>
                                    <span>{aMeta.label}</span>
                                  </span>
                                  {i < (wf.actions?.length || 0) - 1 && (
                                    <span className="text-slate-300 text-[10px]">→</span>
                                  )}
                                </React.Fragment>
                              );
                            })}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Card Bottom: Stats & Action Buttons */}
                    <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                      <div className="text-xs text-slate-500">
                        <span className="font-bold text-slate-700">{wf.total_runs}</span> lượt chạy{' '}
                        <span className="text-slate-300">·</span>{' '}
                        <span className="font-semibold text-emerald-600">{wf.success_rate}%</span> thành công
                      </div>

                      <div className="flex items-center gap-1.5">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setTestRunWorkflow(wf);
                            setTestRunModalOpen(true);
                          }}
                        >
                          🚀 Thử
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleOpenDetail(wf)}
                        >
                          👁️ Chi tiết
                        </Button>
                        <button
                          onClick={() => handleToggleStatus(wf.id, wf.status)}
                          title={isActive ? 'Tạm dừng kịch bản' : 'Bật kích hoạt kịch bản'}
                          className={`p-1.5 rounded-lg border text-xs font-bold transition-colors ${
                            isActive
                              ? 'bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100'
                              : 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100'
                          }`}
                        >
                          {isActive ? '⏸️' : '▶️'}
                        </button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setEditingWorkflow(wf);
                            setFormModalOpen(true);
                          }}
                        >
                          ✏️
                        </Button>
                        {!wf.is_system_template && (
                          <button
                            onClick={() => handleDelete(wf)}
                            title="Xóa kịch bản"
                            className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg transition-colors"
                          >
                            🗑️
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: EXECUTION RUN LOGS */}
      {activeTab === 'runs' && (
        <div className="space-y-4">
          {/* Runs Filter */}
          <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-sm flex items-center gap-3 justify-between">
            <div className="flex items-center gap-3">
              <span className="text-xs font-semibold text-slate-500">Lọc theo trạng thái:</span>
              <select
                value={runsStatusFilter}
                onChange={(e) => setRunsStatusFilter(e.target.value)}
                className="text-xs p-2 rounded-lg border border-slate-200 bg-white"
              >
                <option value="ALL">Tất cả trạng thái</option>
                <option value="SUCCESS">Thành công (SUCCESS)</option>
                <option value="FAILED">Thất bại (FAILED)</option>
                <option value="RUNNING">Đang chạy (RUNNING)</option>
              </select>
            </div>
            <Button variant="outline" size="sm" onClick={fetchRuns}>
              🔄 Làm mới
            </Button>
          </div>

          {/* Runs Table */}
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
            {isRunsLoading ? (
              <div className="p-12 text-center text-slate-400 text-sm">
                Đang tải nhật ký thực thi...
              </div>
            ) : runs.length === 0 ? (
              <div className="p-12 text-center text-slate-500 text-sm">
                Không có lịch sử thực thi nào được ghi nhận.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200 uppercase tracking-wider text-[11px]">
                    <tr>
                      <th className="py-3 px-4">Thời gian</th>
                      <th className="py-3 px-4">Kịch bản</th>
                      <th className="py-3 px-4">Trigger</th>
                      <th className="py-3 px-4">Source ID</th>
                      <th className="py-3 px-4">Số bước</th>
                      <th className="py-3 px-4">Trạng thái</th>
                      <th className="py-3 px-4 text-right">Chi tiết</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {runs.map((r) => (
                      <tr key={r.id} className="hover:bg-slate-50 transition-colors">
                        <td className="py-3 px-4 font-mono text-slate-600">
                          {new Date(r.created_at).toLocaleString('vi-VN')}
                        </td>
                        <td className="py-3 px-4 font-medium text-slate-800">
                          <div>{r.workflow_name || 'N/A'}</div>
                          <div className="font-mono text-[10px] text-slate-400">{r.workflow_code}</div>
                        </td>
                        <td className="py-3 px-4">
                          <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono text-[11px]">
                            {r.trigger_type}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-mono text-slate-500 text-[11px]">
                          {r.trigger_source_id || 'manual'}
                        </td>
                        <td className="py-3 px-4 font-medium text-slate-700">
                          {r.step_count} bước
                        </td>
                        <td className="py-3 px-4">
                          <Badge variant={r.status === 'SUCCESS' ? 'success' : r.status === 'RUNNING' ? 'warning' : 'danger'}>
                            {r.status}
                          </Badge>
                          {r.error_message && (
                            <p className="text-[10px] text-rose-500 line-clamp-1 mt-0.5">{r.error_message}</p>
                          )}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => handleOpenRunDetail(r.id)}
                            className="text-xs font-semibold text-emerald-600 hover:text-emerald-800"
                          >
                            👁️ Xem Log
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Workflow Detail Slide-Over Drawer */}
      <WorkflowDetailDrawer
        workflow={selectedWorkflowDetail}
        isOpen={isDetailDrawerOpen}
        onClose={() => setIsDetailDrawerOpen(false)}
        onTestRun={(w) => {
          setIsDetailDrawerOpen(false);
          setTestRunWorkflow(w);
          setTestRunModalOpen(true);
        }}
        onToggleStatus={handleToggleStatus}
        onEdit={(w) => {
          setIsDetailDrawerOpen(false);
          setEditingWorkflow(w);
          setFormModalOpen(true);
        }}
      />

      {/* Workflow Create / Edit Modal */}
      <WorkflowFormModal
        isOpen={formModalOpen}
        workflow={editingWorkflow}
        onClose={() => {
          setFormModalOpen(false);
          setEditingWorkflow(null);
        }}
        onSuccess={() => {
          fetchWorkflows();
          fetchStats();
        }}
      />

      {/* Workflow Dry-Run Simulator Modal */}
      <WorkflowTestRunModal
        isOpen={testRunModalOpen}
        workflow={testRunWorkflow}
        onClose={() => {
          setTestRunModalOpen(false);
          setTestRunWorkflow(null);
        }}
      />

      {/* Run Detail Modal */}
      {isRunDetailModalOpen && selectedRunDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm" onClick={() => setIsRunDetailModalOpen(false)} />
          <div className="relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
            <div className="p-5 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
              <div>
                <span className="font-mono text-xs text-slate-500">Run ID: {selectedRunDetail.id}</span>
                <h3 className="text-base font-bold text-slate-800 mt-0.5">
                  Chi tiết Lượt chạy: {selectedRunDetail.workflow_name}
                </h3>
              </div>
              <button
                onClick={() => setIsRunDetailModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-2 rounded-lg"
              >
                ✕
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4 flex-1">
              <div className="grid grid-cols-3 gap-3 bg-slate-50 p-3 rounded-xl border border-slate-100 text-xs text-center">
                <div>
                  <span className="text-slate-400">Trạng thái</span>
                  <p className="font-bold text-slate-800">{selectedRunDetail.status}</p>
                </div>
                <div>
                  <span className="text-slate-400">Thời gian bắt đầu</span>
                  <p className="font-mono text-slate-700">{new Date(selectedRunDetail.started_at).toLocaleTimeString('vi-VN')}</p>
                </div>
                <div>
                  <span className="text-slate-400">Thời gian xong</span>
                  <p className="font-mono text-slate-700">
                    {selectedRunDetail.completed_at ? new Date(selectedRunDetail.completed_at).toLocaleTimeString('vi-VN') : '-'}
                  </p>
                </div>
              </div>

              {selectedRunDetail.error_message && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-xs">
                  <span className="font-bold">Lỗi:</span> {selectedRunDetail.error_message}
                </div>
              )}

              <div>
                <h4 className="text-xs font-bold text-slate-700 uppercase mb-2">Các bước đã thực thi ({selectedRunDetail.step_runs?.length || 0}):</h4>
                <div className="space-y-2">
                  {selectedRunDetail.step_runs?.map((step) => (
                    <div key={step.step_index} className="p-3 bg-white rounded-xl border border-slate-200 text-xs">
                      <div className="flex items-center justify-between font-semibold text-slate-800 mb-1">
                        <span>Bước {step.step_index}: {step.action_type}</span>
                        <span className={`text-[11px] font-bold ${step.status === 'SUCCESS' ? 'text-emerald-600' : 'text-rose-600'}`}>
                          {step.status}
                        </span>
                      </div>
                      {step.output && (
                        <pre className="text-[11px] font-mono text-slate-600 bg-slate-50 p-2 rounded overflow-x-auto mt-1">
                          {JSON.stringify(step.output, null, 2)}
                        </pre>
                      )}
                      {step.error && (
                        <p className="text-[11px] text-rose-600 mt-1 font-mono">Lỗi: {step.error}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {selectedRunDetail.metadata_json && Object.keys(selectedRunDetail.metadata_json).length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-slate-700 uppercase mb-1">Ngữ cảnh đầu vào (Context):</h4>
                  <pre className="text-[11px] font-mono text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-200 overflow-x-auto">
                    {JSON.stringify(selectedRunDetail.metadata_json, null, 2)}
                  </pre>
                </div>
              )}
            </div>

            <div className="p-4 border-t border-slate-100 bg-slate-50 flex justify-end">
              <Button variant="outline" size="sm" onClick={() => setIsRunDetailModalOpen(false)}>
                Đóng
              </Button>
            </div>
          </div>
        </div>
      )}
    </AdminShell>
  );
}
