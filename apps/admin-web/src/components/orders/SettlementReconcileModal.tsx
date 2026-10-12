'use client';

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  Button,
  Input,
  Select,
  Badge,
} from '@moc-healthy/ui';
import {
  SettlementResponse,
  SettlementReconcileResult,
} from '@moc-healthy/contracts';
import { omnichannelApi } from '../../lib/api';

export interface SettlementReconcileModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSettlementUpdated?: () => void;
}

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
    maximumFractionDigits: 0,
  }).format(amount);
};

const formatDate = (isoString?: string | null) => {
  if (!isoString) return '---';
  try {
    const d = new Date(isoString);
    return d.toLocaleDateString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return isoString;
  }
};

export const SettlementReconcileModal: React.FC<SettlementReconcileModalProps> = ({
  isOpen,
  onClose,
  onSettlementUpdated,
}) => {
  const [activeTab, setActiveTab] = useState<'LIST' | 'CREATE'>('LIST');
  const [channelFilter, setChannelFilter] = useState<string>('ALL');
  const [settlements, setSettlements] = useState<SettlementResponse[]>([]);
  const [isLoadingList, setIsLoadingList] = useState(false);

  // Form State
  const [channel, setChannel] = useState<'GRAB' | 'SHOPEEFOOD' | 'MANUAL'>('GRAB');
  const [externalSettlementId, setExternalSettlementId] = useState('');
  const [periodStart, setPeriodStart] = useState('2026-10-01T00:00');
  const [periodEnd, setPeriodEnd] = useState('2026-10-31T23:59');
  const [grossAmount, setGrossAmount] = useState<number>(440000);
  const [platformFee, setPlatformFee] = useState<number>(88000);
  const [merchantDiscount, setMerchantDiscount] = useState<number>(15000);
  const [otherFee, setOtherFee] = useState<number>(0);
  const [notes, setNotes] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [reconcilingId, setReconcilingId] = useState<string | null>(null);
  const [reconcileResult, setReconcileResult] = useState<SettlementReconcileResult | null>(null);
  const [feedbackMessage, setFeedbackMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const calculatedNet = Math.max(0, grossAmount - platformFee - merchantDiscount - otherFee);

  const loadSettlements = async () => {
    setIsLoadingList(true);
    try {
      const data = await omnichannelApi.listSettlements({
        channel: channelFilter === 'ALL' ? undefined : channelFilter,
      });
      setSettlements(data);
    } catch (err: any) {
      setFeedbackMessage({ type: 'error', text: err.message || 'Lỗi tải danh sách đối soát' });
    } finally {
      setIsLoadingList(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadSettlements();
      setReconcileResult(null);
      setFeedbackMessage(null);
    }
  }, [isOpen, channelFilter]);

  const handleFillDemo = (type: 'GRAB' | 'SHOPEEFOOD') => {
    if (type === 'GRAB') {
      setChannel('GRAB');
      setExternalSettlementId(`ST-GRAB-${Date.now().toString().slice(-4)}`);
      setPeriodStart('2026-10-01T00:00');
      setPeriodEnd('2026-10-31T23:59');
      setGrossAmount(440000);
      setPlatformFee(88000);
      setMerchantDiscount(15000);
      setOtherFee(0);
      setNotes('Sao kê tuần 1 tháng 10/2026 từ Grab Merchant Portal');
    } else {
      setChannel('SHOPEEFOOD');
      setExternalSettlementId(`ST-SPF-${Date.now().toString().slice(-4)}`);
      setPeriodStart('2026-10-01T00:00');
      setPeriodEnd('2026-10-31T23:59');
      setGrossAmount(420000);
      setPlatformFee(105000);
      setMerchantDiscount(20000);
      setOtherFee(0);
      setNotes('Sao kê đối soát ShopeeFood tháng 10/2026');
    }
  };

  const handleCreateSettlement = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!externalSettlementId.trim()) {
      setFeedbackMessage({ type: 'error', text: 'Vui lòng nhập mã đối soát sàn' });
      return;
    }
    setIsSubmitting(true);
    setFeedbackMessage(null);
    try {
      await omnichannelApi.createSettlement({
        channel,
        external_settlement_id: externalSettlementId.trim(),
        period_start: new Date(periodStart).toISOString(),
        period_end: new Date(periodEnd).toISOString(),
        gross_amount: Number(grossAmount),
        platform_fee: Number(platformFee),
        merchant_discount: Number(merchantDiscount),
        other_fee: Number(otherFee),
        notes: notes.trim() || undefined,
      });

      setFeedbackMessage({ type: 'success', text: 'Tạo kỳ đối soát thành công!' });
      setActiveTab('LIST');
      await loadSettlements();
      if (onSettlementUpdated) onSettlementUpdated();
    } catch (err: any) {
      setFeedbackMessage({ type: 'error', text: err.message || 'Lỗi khi tạo kỳ đối soát' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReconcile = async (id: string) => {
    setReconcilingId(id);
    setFeedbackMessage(null);
    setReconcileResult(null);
    try {
      const result = await omnichannelApi.reconcileSettlement(id);
      setReconcileResult(result);
      setFeedbackMessage({
        type: 'success',
        text: `Đối soát hoàn tất: Khớp ${result.matched_orders}/${result.total_orders_in_period} đơn (${result.status === 'MATCHED' ? 'Khớp 100%' : 'Chênh lệch: ' + formatCurrency(result.discrepancy)})`,
      });
      await loadSettlements();
      if (onSettlementUpdated) onSettlementUpdated();
    } catch (err: any) {
      setFeedbackMessage({ type: 'error', text: err.message || 'Lỗi trong quá trình đối soát' });
    } finally {
      setReconcilingId(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'MATCHED':
        return <Badge variant="success">✅ Khớp 100%</Badge>;
      case 'PARTIAL':
        return <Badge variant="warning">⚠️ Lệch số liệu</Badge>;
      case 'DISPUTED':
        return <Badge variant="danger">❌ Tranh chấp</Badge>;
      default:
        return <Badge variant="neutral">⏳ Chưa đối soát</Badge>;
    }
  };

  const getChannelBadge = (ch: string) => {
    switch (ch) {
      case 'GRAB':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800">GrabFood</span>;
      case 'SHOPEEFOOD':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-orange-100 text-orange-800">ShopeeFood</span>;
      default:
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-800">{ch}</span>;
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="⚖️ Đối soát Doanh thu Sàn & Báo cáo Net (Settlement Hub)"
      maxWidth="xl"
    >
      <div className="space-y-6">
        {/* Navigation Tabs */}
        <div className="flex border-b border-slate-200">
          <button
            type="button"
            className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors ${
              activeTab === 'LIST'
                ? 'border-emerald-600 text-emerald-700'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
            onClick={() => setActiveTab('LIST')}
          >
            📋 Danh sách kỳ đối soát ({settlements.length})
          </button>
          <button
            type="button"
            className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors ${
              activeTab === 'CREATE'
                ? 'border-emerald-600 text-emerald-700'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
            onClick={() => setActiveTab('CREATE')}
          >
            ➕ Tạo kỳ đối soát từ sao kê sàn
          </button>
        </div>

        {/* Global Feedback Message */}
        {feedbackMessage && (
          <div
            className={`p-3 rounded-lg text-sm flex items-center justify-between ${
              feedbackMessage.type === 'success'
                ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                : 'bg-rose-50 text-rose-800 border border-rose-200'
            }`}
          >
            <span>{feedbackMessage.text}</span>
            <button
              type="button"
              onClick={() => setFeedbackMessage(null)}
              className="text-xs underline ml-2 font-medium"
            >
              Đóng
            </button>
          </div>
        )}

        {/* Reconcile Result Summary Card */}
        {reconcileResult && (
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-900 text-sm">
                Kết quả đối soát kỳ: {reconcileResult.settlement_id}
              </span>
              {getStatusBadge(reconcileResult.status)}
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
              <div className="bg-white p-2.5 rounded-lg border border-slate-100">
                <p className="text-slate-500">Đơn trong kỳ</p>
                <p className="font-bold text-slate-800 text-sm">{reconcileResult.total_orders_in_period} đơn</p>
              </div>
              <div className="bg-white p-2.5 rounded-lg border border-slate-100">
                <p className="text-slate-500">Đơn khớp</p>
                <p className="font-bold text-emerald-700 text-sm">{reconcileResult.matched_orders} đơn</p>
              </div>
              <div className="bg-white p-2.5 rounded-lg border border-slate-100">
                <p className="text-slate-500">Sao kê sàn (Net)</p>
                <p className="font-bold text-slate-900 text-sm">{formatCurrency(reconcileResult.total_settlement_net)}</p>
              </div>
              <div className="bg-white p-2.5 rounded-lg border border-slate-100">
                <p className="text-slate-500">Chênh lệch đối soát</p>
                <p className={`font-bold text-sm ${reconcileResult.discrepancy === 0 ? 'text-emerald-700' : 'text-amber-600'}`}>
                  {formatCurrency(reconcileResult.discrepancy)}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* TAB 1: LIST SETTLEMENTS */}
        {activeTab === 'LIST' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-600">Lọc kênh:</span>
                <Select
                  value={channelFilter}
                  onChange={(e) => setChannelFilter(e.target.value)}
                  options={[
                    { value: 'ALL', label: 'Tất cả các kênh' },
                    { value: 'GRAB', label: 'GrabFood' },
                    { value: 'SHOPEEFOOD', label: 'ShopeeFood' },
                    { value: 'MANUAL', label: 'Kênh khác (Manual)' },
                  ]}
                />
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={loadSettlements}
                disabled={isLoadingList}
              >
                🔄 Làm mới
              </Button>
            </div>

            {isLoadingList ? (
              <div className="py-12 text-center text-slate-500 text-sm">
                Đang tải danh sách kỳ đối soát...
              </div>
            ) : settlements.length === 0 ? (
              <div className="py-12 text-center bg-slate-50 border border-dashed border-slate-200 rounded-xl space-y-3">
                <p className="text-slate-600 text-sm">Chưa có bản ghi đối soát nào cho kênh này.</p>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => {
                    handleFillDemo('GRAB');
                    setActiveTab('CREATE');
                  }}
                >
                  ⚡ Nạp thử sao kê GrabFood
                </Button>
              </div>
            ) : (
              <div className="overflow-x-auto border border-slate-200 rounded-xl">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                    <tr>
                      <th className="py-2.5 px-3">Mã kỳ đối soát</th>
                      <th className="py-2.5 px-3">Kênh sàn</th>
                      <th className="py-2.5 px-3">Kỳ báo cáo</th>
                      <th className="py-2.5 px-3 text-right">Doanh thu gộp</th>
                      <th className="py-2.5 px-3 text-right">Phí sàn</th>
                      <th className="py-2.5 px-3 text-right">Thực nhận sao kê</th>
                      <th className="py-2.5 px-3 text-center">Trạng thái</th>
                      <th className="py-2.5 px-3 text-center">Hành động</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {settlements.map((item) => (
                      <tr key={item.id} className="hover:bg-slate-50/70 transition-colors">
                        <td className="py-2.5 px-3">
                          <span className="font-mono font-bold text-slate-800">
                            {item.external_settlement_id || item.id.slice(0, 8)}
                          </span>
                          {item.notes && (
                            <p className="text-[11px] text-slate-400 truncate max-w-[160px]">
                              {item.notes}
                            </p>
                          )}
                        </td>
                        <td className="py-2.5 px-3">{getChannelBadge(item.channel)}</td>
                        <td className="py-2.5 px-3 text-slate-600 whitespace-nowrap">
                          {formatDate(item.period_start)}
                          <br />
                          <span className="text-slate-400">đến</span> {formatDate(item.period_end)}
                        </td>
                        <td className="py-2.5 px-3 text-right font-medium text-slate-800">
                          {formatCurrency(item.gross_amount)}
                        </td>
                        <td className="py-2.5 px-3 text-right text-rose-600 font-medium">
                          -{formatCurrency(item.platform_fee)}
                        </td>
                        <td className="py-2.5 px-3 text-right font-bold text-emerald-700">
                          {formatCurrency(item.net_amount)}
                        </td>
                        <td className="py-2.5 px-3 text-center">
                          {getStatusBadge(item.status)}
                          {item.matched_orders_count > 0 && (
                            <div className="text-[10px] text-slate-500 mt-0.5">
                              {item.matched_orders_count} đơn khớp
                            </div>
                          )}
                        </td>
                        <td className="py-2.5 px-3 text-center whitespace-nowrap">
                          <Button
                            variant="primary"
                            size="sm"
                            disabled={reconcilingId === item.id}
                            onClick={() => handleReconcile(item.id)}
                          >
                            {reconcilingId === item.id ? 'Đang khớp...' : '⚡ Khớp đối soát'}
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: CREATE SETTLEMENT */}
        {activeTab === 'CREATE' && (
          <form onSubmit={handleCreateSettlement} className="space-y-5">
            <div className="flex items-center justify-between bg-slate-50 p-3 rounded-lg border border-slate-200">
              <span className="text-xs text-slate-600 font-medium">
                Mẹo: Điền nhanh dữ liệu mẫu sao kê đã nhập đơn để thử đối soát tự động:
              </span>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => handleFillDemo('GRAB')}
                >
                  GrabFood Mẫu
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => handleFillDemo('SHOPEEFOOD')}
                >
                  ShopeeFood Mẫu
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Kênh bán hàng <span className="text-rose-500">*</span>
                </label>
                <Select
                  value={channel}
                  onChange={(e) => setChannel(e.target.value as any)}
                  options={[
                    { value: 'GRAB', label: 'GrabFood' },
                    { value: 'SHOPEEFOOD', label: 'ShopeeFood' },
                    { value: 'MANUAL', label: 'Kênh khác (Manual POS/Đối soát nội bộ)' },
                  ]}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Mã kỳ đối soát sàn (External Settlement ID) <span className="text-rose-500">*</span>
                </label>
                <Input
                  value={externalSettlementId}
                  onChange={(e) => setExternalSettlementId(e.target.value)}
                  placeholder="Ví dụ: ST-GRAB-202610-W1"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Bắt đầu kỳ đối soát <span className="text-rose-500">*</span>
                </label>
                <Input
                  type="datetime-local"
                  value={periodStart}
                  onChange={(e) => setPeriodStart(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Kết thúc kỳ đối soát <span className="text-rose-500">*</span>
                </label>
                <Input
                  type="datetime-local"
                  value={periodEnd}
                  onChange={(e) => setPeriodEnd(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="p-4 bg-emerald-50/50 border border-emerald-200 rounded-xl space-y-4">
              <h4 className="text-xs font-bold text-emerald-900 uppercase tracking-wider">
                Số liệu tài chính theo sao kê sàn
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Doanh thu gộp (Gross)
                  </label>
                  <Input
                    type="number"
                    min={0}
                    value={grossAmount}
                    onChange={(e) => setGrossAmount(Number(e.target.value))}
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Chiết khấu sàn (Commission)
                  </label>
                  <Input
                    type="number"
                    min={0}
                    value={platformFee}
                    onChange={(e) => setPlatformFee(Number(e.target.value))}
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Khuyến mãi quán chịu
                  </label>
                  <Input
                    type="number"
                    min={0}
                    value={merchantDiscount}
                    onChange={(e) => setMerchantDiscount(Number(e.target.value))}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Phí dịch vụ khác
                  </label>
                  <Input
                    type="number"
                    min={0}
                    value={otherFee}
                    onChange={(e) => setOtherFee(Number(e.target.value))}
                  />
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-emerald-200 text-sm">
                <span className="font-semibold text-emerald-900">
                  Doanh thu thực nhận sàn dự kiến (Net Settlement):
                </span>
                <span className="text-base font-extrabold text-emerald-700 font-mono">
                  {formatCurrency(calculatedNet)}
                </span>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Ghi chú kỳ đối soát
              </label>
              <Input
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Ví dụ: Kỳ thanh toán định kỳ thứ Tư hàng tuần"
              />
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-200">
              <Button
                type="button"
                variant="outline"
                onClick={() => setActiveTab('LIST')}
                disabled={isSubmitting}
              >
                Hủy
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Đang lưu...' : '💾 Lưu kỳ đối soát'}
              </Button>
            </div>
          </form>
        )}
      </div>
    </Dialog>
  );
};
