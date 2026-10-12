'use client';

import React, { useState, useEffect } from 'react';
import { Dialog, Button, Input, Select } from '@moc-healthy/ui';
import {
  CampaignDetailResponse,
  CampaignCreateInput,
  CampaignUpdateInput,
  MarketingChannel,
  CampaignObjective,
} from '@moc-healthy/contracts';
import { campaignsApi, productsApi, promotionsApi } from '../../lib/api';

export interface CampaignFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  campaign?: CampaignDetailResponse | null;
  onSuccess: () => void;
}

interface ChannelRow {
  channel: string;
  channel_budget: number;
  target_metric: string;
  notes: string;
}

interface ProductRow {
  product_id: string;
  is_hero_product: boolean;
  special_price?: number;
}

const AVAILABLE_SEGMENTS = [
  { value: 'VIP', label: '👑 VIP (Thân thiết)' },
  { value: 'ACTIVE', label: '🟢 ACTIVE (Đang tương tác)' },
  { value: 'REPEAT', label: '🔄 REPEAT (Quay lại)' },
  { value: 'NEW', label: '✨ NEW (Khách hàng mới)' },
  { value: 'AT_RISK', label: '⚠️ AT_RISK (Có nguy cơ rời bỏ)' },
  { value: 'HIGH_VALUE', label: '💎 HIGH_VALUE (Giá trị đơn cao)' },
];

const AVAILABLE_CHANNELS = [
  { value: 'FACEBOOK', label: 'Facebook Ads' },
  { value: 'ZALO', label: 'Zalo OA / ZNS' },
  { value: 'TIKTOK', label: 'TikTok Ads' },
  { value: 'INSTAGRAM', label: 'Instagram' },
  { value: 'SMS', label: 'SMS Brandname' },
  { value: 'EMAIL', label: 'Email Marketing' },
  { value: 'WEBSITE_BANNER', label: 'Website Banner' },
];

export const CampaignFormModal: React.FC<CampaignFormModalProps> = ({
  isOpen,
  onClose,
  campaign,
  onSuccess,
}) => {
  const isEditing = !!campaign;

  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [objective, setObjective] = useState<CampaignObjective>('CONVERSION');
  const [startAt, setStartAt] = useState('');
  const [endAt, setEndAt] = useState('');
  const [budget, setBudget] = useState<number>(5000000);
  const [selectedAudiences, setSelectedAudiences] = useState<string[]>(['ACTIVE', 'REPEAT']);
  const [promotionId, setPromotionId] = useState<string>('');
  const [landingPage, setLandingPage] = useState('');
  const [utmSource, setUtmSource] = useState('facebook');
  const [utmMedium, setUtmMedium] = useState('cpc');
  const [utmCampaign, setUtmCampaign] = useState('');
  const [notes, setNotes] = useState('');

  // Channels & Products
  const [channels, setChannels] = useState<ChannelRow[]>([
    { channel: 'FACEBOOK', channel_budget: 3000000, target_metric: '200 conversions', notes: '' },
    { channel: 'ZALO', channel_budget: 2000000, target_metric: '100 orders', notes: '' },
  ]);
  const [productRows, setProductRows] = useState<ProductRow[]>([]);

  // Selection list options
  const [productsList, setProductsList] = useState<Array<{ id: string; name: string; price: number }>>([]);
  const [promotionsList, setPromotionsList] = useState<Array<{ id: string; name: string; code: string }>>([]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Load available products and promotions for dropdowns
  useEffect(() => {
    if (isOpen) {
      loadDependencies();
    }
  }, [isOpen]);

  const loadDependencies = async () => {
    try {
      const [prodsRes, promosRes] = await Promise.all([
        productsApi.list({ page_size: 50 }),
        promotionsApi.list({ status: 'ACTIVE', page_size: 50 }),
      ]);
      setProductsList(
        prodsRes.items.map((p) => ({
          id: p.id,
          name: p.name,
          price: p.sale_price || p.base_price,
        }))
      );
      setPromotionsList(
        promosRes.items.map((pr) => ({
          id: pr.id,
          name: pr.title,
          code: pr.code || '',
        }))
      );
    } catch {
      // Fallback
    }
  };

  useEffect(() => {
    if (campaign) {
      setName(campaign.name);
      setCode(campaign.code);
      setObjective(campaign.objective as CampaignObjective);
      setStartAt(campaign.start_at ? campaign.start_at.slice(0, 16) : '');
      setEndAt(campaign.end_at ? campaign.end_at.slice(0, 16) : '');
      setBudget(campaign.budget || 0);
      setSelectedAudiences(campaign.target_audience || []);
      setPromotionId(campaign.promotion_id || '');
      setLandingPage(campaign.landing_page || '');
      setUtmSource(campaign.utm_source || 'facebook');
      setUtmMedium(campaign.utm_medium || 'cpc');
      setUtmCampaign(campaign.utm_campaign || '');
      setNotes(campaign.notes || '');

      if (campaign.channels && campaign.channels.length > 0) {
        setChannels(
          campaign.channels.map((c) => ({
            channel: c.channel,
            channel_budget: c.channel_budget,
            target_metric: c.target_metric || '',
            notes: c.notes || '',
          }))
        );
      } else {
        setChannels([]);
      }

      if (campaign.products && campaign.products.length > 0) {
        setProductRows(
          campaign.products.map((p) => ({
            product_id: p.product_id,
            is_hero_product: p.is_hero_product,
            special_price: p.special_price || undefined,
          }))
        );
      } else {
        setProductRows([]);
      }
    } else {
      // Defaults for new campaign
      const now = new Date();
      const in7Days = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
      const in21Days = new Date(now.getTime() + 21 * 24 * 60 * 60 * 1000);

      setName('');
      setCode(`CAMP-${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}-${Math.floor(100 + Math.random() * 900)}`);
      setObjective('CONVERSION');
      setStartAt(in7Days.toISOString().slice(0, 16));
      setEndAt(in21Days.toISOString().slice(0, 16));
      setBudget(10000000);
      setSelectedAudiences(['ACTIVE', 'REPEAT', 'VIP']);
      setPromotionId('');
      setLandingPage('');
      setUtmSource('facebook');
      setUtmMedium('cpc');
      setUtmCampaign('');
      setNotes('');
      setChannels([
        { channel: 'FACEBOOK', channel_budget: 6000000, target_metric: '400 conversions', notes: '' },
        { channel: 'ZALO', channel_budget: 4000000, target_metric: '150 orders', notes: '' },
      ]);
      setProductRows([]);
    }
    setErrorMessage(null);
  }, [campaign, isOpen]);

  const toggleAudience = (seg: string) => {
    setSelectedAudiences((prev) =>
      prev.includes(seg) ? prev.filter((s) => s !== seg) : [...prev, seg]
    );
  };

  const handleAddChannel = () => {
    setChannels((prev) => [
      ...prev,
      { channel: 'TIKTOK', channel_budget: 2000000, target_metric: '', notes: '' },
    ]);
  };

  const handleRemoveChannel = (index: number) => {
    setChannels((prev) => prev.filter((_, i) => i !== index));
  };

  const handleChannelChange = (index: number, field: keyof ChannelRow, value: any) => {
    setChannels((prev) => {
      const copy = [...prev];
      copy[index] = { ...copy[index], [field]: value };
      return copy;
    });
  };

  const handleAddProduct = () => {
    if (productsList.length > 0) {
      setProductRows((prev) => [
        ...prev,
        { product_id: productsList[0].id, is_hero_product: prev.length === 0 },
      ]);
    }
  };

  const handleRemoveProduct = (index: number) => {
    setProductRows((prev) => prev.filter((_, i) => i !== index));
  };

  const handleProductChange = (index: number, field: keyof ProductRow, value: any) => {
    setProductRows((prev) => {
      const copy = [...prev];
      copy[index] = { ...copy[index], [field]: value };
      return copy;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setErrorMessage('Vui lòng nhập tên chiến dịch');
      return;
    }
    if (!code.trim()) {
      setErrorMessage('Vui lòng nhập mã chiến dịch');
      return;
    }
    if (!startAt || !endAt) {
      setErrorMessage('Vui lòng chọn thời gian bắt đầu và kết thúc');
      return;
    }
    if (new Date(endAt) <= new Date(startAt)) {
      setErrorMessage('Thời gian kết thúc phải sau thời gian bắt đầu');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const payloadChannels = channels.map((c) => ({
        channel: c.channel,
        channel_budget: Number(c.channel_budget) || 0,
        target_metric: c.target_metric.trim() || null,
        notes: c.notes.trim() || null,
      }));

      const payloadProducts = productRows.map((p) => ({
        product_id: p.product_id,
        is_hero_product: p.is_hero_product,
        special_price: p.special_price ? Number(p.special_price) : null,
      }));

      if (isEditing && campaign) {
        const updateData: CampaignUpdateInput = {
          name: name.trim(),
          objective,
          start_at: new Date(startAt).toISOString(),
          end_at: new Date(endAt).toISOString(),
          budget: Number(budget) || 0,
          target_audience: selectedAudiences,
          promotion_id: promotionId ? promotionId : null,
          landing_page: landingPage.trim() || null,
          notes: notes.trim() || null,
          channels: payloadChannels,
          products: payloadProducts,
        };
        await campaignsApi.update(campaign.id, updateData);
      } else {
        const createData: CampaignCreateInput = {
          name: name.trim(),
          code: code.trim().toUpperCase(),
          objective,
          start_at: new Date(startAt).toISOString(),
          end_at: new Date(endAt).toISOString(),
          budget: Number(budget) || 0,
          target_audience: selectedAudiences,
          promotion_id: promotionId ? promotionId : null,
          landing_page: landingPage.trim() || null,
          utm_source: utmSource.trim() || null,
          utm_medium: utmMedium.trim() || null,
          utm_campaign: utmCampaign.trim() || code.trim().toLowerCase(),
          notes: notes.trim() || null,
          channels: payloadChannels,
          products: payloadProducts,
        };
        await campaignsApi.create(createData);
      }

      onSuccess();
      onClose();
    } catch (err: any) {
      setErrorMessage(err.message || 'Có lỗi xảy ra khi lưu chiến dịch');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title={isEditing ? `Chỉnh sửa chiến dịch: ${campaign?.name}` : 'Thiết lập chiến dịch tiếp thị mới'}
    >
      <form onSubmit={handleSubmit} className="space-y-4 max-h-[75vh] overflow-y-auto px-1">
        {errorMessage && (
          <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg">
            {errorMessage}
          </div>
        )}

        {/* Basic Info */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <Input
            label="Tên chiến dịch *"
            placeholder="vd: Năng Lượng Xanh Mùa Thu"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <Input
            label="Mã định danh (Code) *"
            placeholder="vd: CAMP-AUTUMN-2026"
            value={code}
            onChange={(e) => setCode(e.target.value.toUpperCase())}
            disabled={isEditing}
            required
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <Select
            label="Mục tiêu chiến dịch (Objective)"
            value={objective}
            onChange={(e) => setObjective(e.target.value as CampaignObjective)}
            options={[
              { value: 'CONVERSION', label: '🎯 Tăng chuyển đổi đơn hàng (CONVERSION)' },
              { value: 'AWARENESS', label: '📢 Tăng nhận diện thương hiệu (AWARENESS)' },
              { value: 'CLEARANCE', label: '⚡ Xả kho sản phẩm cận date (CLEARANCE)' },
              { value: 'LOYALTY', label: '👑 Tri ân khách hàng thân thiết (LOYALTY)' },
              { value: 'REENGAGEMENT', label: '🔄 Kích hoạt lại khách hàng cũ (REENGAGEMENT)' },
            ]}
          />
          <Input
            label="Ngân sách dự toán (VNĐ) *"
            type="number"
            min={0}
            step={500000}
            value={budget}
            onChange={(e) => setBudget(Number(e.target.value))}
            required
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <Input
            label="Thời gian bắt đầu *"
            type="datetime-local"
            value={startAt}
            onChange={(e) => setStartAt(e.target.value)}
            required
          />
          <Input
            label="Thời gian kết thúc *"
            type="datetime-local"
            value={endAt}
            onChange={(e) => setEndAt(e.target.value)}
            required
          />
        </div>

        {/* Target Audience */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5">
            Phân khúc khách hàng mục tiêu
          </label>
          <div className="flex flex-wrap gap-2">
            {AVAILABLE_SEGMENTS.map((seg) => {
              const active = selectedAudiences.includes(seg.value);
              return (
                <button
                  type="button"
                  key={seg.value}
                  onClick={() => toggleAudience(seg.value)}
                  className={`px-2.5 py-1 text-xs rounded-full border transition-all ${
                    active
                      ? 'bg-emerald-600 text-white border-emerald-600 font-medium shadow-xs'
                      : 'bg-slate-50 text-slate-700 border-slate-300 hover:bg-slate-100'
                  }`}
                >
                  {seg.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Linked Promotion */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <Select
            label="Voucher / Khuyến mãi liên kết (tùy chọn)"
            value={promotionId}
            onChange={(e) => setPromotionId(e.target.value)}
            options={[
              { value: '', label: '-- Không áp dụng ưu đãi liên kết --' },
              ...promotionsList.map((pr) => ({
                value: pr.id,
                label: `🎁 ${pr.code} - ${pr.name}`,
              })),
            ]}
          />
          <Input
            label="Landing page URL"
            placeholder="https://mochanh.vn/collections/autumn"
            value={landingPage}
            onChange={(e) => setLandingPage(e.target.value)}
          />
        </div>

        {/* Tracking UTM */}
        <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
          <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider block mb-2">
            Tracking UTM Tham số
          </span>
          <div className="grid grid-cols-3 gap-2">
            <Input
              label="utm_source"
              value={utmSource}
              onChange={(e) => setUtmSource(e.target.value)}
              placeholder="facebook"
            />
            <Input
              label="utm_medium"
              value={utmMedium}
              onChange={(e) => setUtmMedium(e.target.value)}
              placeholder="cpc"
            />
            <Input
              label="utm_campaign"
              value={utmCampaign}
              onChange={(e) => setUtmCampaign(e.target.value)}
              placeholder="autumn_2026"
            />
          </div>
        </div>

        {/* Marketing Channels */}
        <div className="border border-slate-200 rounded-lg p-3">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-bold text-slate-700">Kênh truyền thông phân phối</span>
            <Button type="button" variant="outline" size="sm" onClick={handleAddChannel}>
              + Thêm kênh
            </Button>
          </div>
          {channels.length === 0 ? (
            <p className="text-xs text-slate-400 italic">Chưa chọn kênh phân phối</p>
          ) : (
            <div className="space-y-2">
              {channels.map((ch, idx) => (
                <div key={idx} className="flex flex-wrap items-center gap-2 p-2 bg-slate-50 rounded border border-slate-200 text-xs">
                  <div className="w-32">
                    <Select
                      value={ch.channel}
                      onChange={(e) => handleChannelChange(idx, 'channel', e.target.value)}
                      options={AVAILABLE_CHANNELS}
                    />
                  </div>
                  <div className="w-28">
                    <Input
                      type="number"
                      step={500000}
                      placeholder="Ngân sách"
                      value={ch.channel_budget}
                      onChange={(e) => handleChannelChange(idx, 'channel_budget', Number(e.target.value))}
                    />
                  </div>
                  <div className="flex-1 min-w-[140px]">
                    <Input
                      placeholder="KPI: 200 conversions..."
                      value={ch.target_metric}
                      onChange={(e) => handleChannelChange(idx, 'target_metric', e.target.value)}
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRemoveChannel(idx)}
                    className="text-rose-500 hover:text-rose-700 font-bold px-1"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Hero Products */}
        <div className="border border-slate-200 rounded-lg p-3">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-bold text-slate-700">Sản phẩm trọng tâm (Hero Products)</span>
            <Button type="button" variant="outline" size="sm" onClick={handleAddProduct}>
              + Gắn sản phẩm
            </Button>
          </div>
          {productRows.length === 0 ? (
            <p className="text-xs text-slate-400 italic">Chưa chọn sản phẩm hero cụ thể (áp dụng toàn menu)</p>
          ) : (
            <div className="space-y-2">
              {productRows.map((pr, idx) => (
                <div key={idx} className="flex flex-wrap items-center gap-2 p-2 bg-slate-50 rounded border border-slate-200 text-xs">
                  <div className="flex-1 min-w-[160px]">
                    <Select
                      value={pr.product_id}
                      onChange={(e) => handleProductChange(idx, 'product_id', e.target.value)}
                      options={productsList.map((p) => ({ value: p.id, label: p.name }))}
                    />
                  </div>
                  <label className="flex items-center gap-1 cursor-pointer font-medium text-slate-700">
                    <input
                      type="checkbox"
                      checked={pr.is_hero_product}
                      onChange={(e) => handleProductChange(idx, 'is_hero_product', e.target.checked)}
                      className="rounded text-emerald-600 focus:ring-emerald-500"
                    />
                    ⭐ Hero
                  </label>
                  <div className="w-28">
                    <Input
                      type="number"
                      placeholder="Giá ưu đãi"
                      value={pr.special_price || ''}
                      onChange={(e) => handleProductChange(idx, 'special_price', e.target.value ? Number(e.target.value) : undefined)}
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRemoveProduct(idx)}
                    className="text-rose-500 hover:text-rose-700 font-bold px-1"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <Input
          label="Ghi chú chiến lược nội bộ"
          placeholder="Mục tiêu chính, định hướng thông điệp, chỉ dẫn đội ngũ..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />

        {/* Actions */}
        <div className="flex justify-end gap-2 pt-3 border-t border-slate-200">
          <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting}>
            Hủy
          </Button>
          <Button type="submit" variant="primary" disabled={isSubmitting}>
            {isSubmitting ? 'Đang lưu...' : isEditing ? 'Cập nhật chiến dịch' : 'Tạo bản nháp chiến dịch'}
          </Button>
        </div>
      </form>
    </Dialog>
  );
};
