'use client';

import React, { useState, useEffect } from 'react';
import { Dialog, Button, Input, Select } from '@moc-healthy/ui';
import {
  ContentDetailResponse,
  ContentCreateInput,
  ContentUpdateInput,
  ContentType,
  ContentChannel,
  BrandTone,
} from '@moc-healthy/contracts';
import { contentApi, productsApi, campaignsApi } from '../../lib/api';

export interface ContentFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  item?: ContentDetailResponse | null;
  onSuccess: () => void;
}

const AVAILABLE_CHANNELS = [
  { value: 'FACEBOOK', label: '📘 Facebook' },
  { value: 'INSTAGRAM', label: '📷 Instagram' },
  { value: 'TIKTOK', label: '🎵 TikTok' },
  { value: 'ZALO', label: '💬 Zalo OA' },
  { value: 'WEBSITE_BANNER', label: '🌐 Website Banner' },
];

const AVAILABLE_TYPES = [
  { value: 'FACEBOOK_POST', label: 'Bài đăng Facebook Post' },
  { value: 'INSTAGRAM_POST', label: 'Bài đăng Instagram Post' },
  { value: 'TIKTOK_SCRIPT', label: 'Kịch bản video TikTok (45s)' },
  { value: 'REEL_SCRIPT', label: 'Kịch bản Instagram Reel (30s)' },
  { value: 'ZALO_MESSAGE', label: 'Tin nhắn Zalo OA / ZNS' },
  { value: 'WEBSITE_BANNER_COPY', label: 'Tiêu đề & Banner website' },
  { value: 'PRODUCT_STORY', label: 'Câu chuyện sản phẩm (Storytelling)' },
  { value: 'SEO_ARTICLE', label: 'Bài viết chuẩn SEO' },
];

const AVAILABLE_TONES = [
  { value: 'FRESH_ENERGETIC', label: '🌱 Tươi mới, tràn đầy năng lượng' },
  { value: 'NUTRITION_EXPERT', label: '🔬 Chuyên gia dinh dưỡng tin cậy' },
  { value: 'WARM_FRIENDLY', label: '💖 Gần gũi, ấm áp, chăm sóc' },
  { value: 'MINIMAL_HEALTHY', label: '🧘 Tối giản, thanh lọc cơ thể' },
  { value: 'TRENDY_HUMOR', label: '⚡ Trẻ trung, bắt trend, hài hước' },
];

export const ContentFormModal: React.FC<ContentFormModalProps> = ({
  isOpen,
  onClose,
  item,
  onSuccess,
}) => {
  const isEditing = !!item;

  const [title, setTitle] = useState('');
  const [contentType, setContentType] = useState<ContentType>('FACEBOOK_POST');
  const [channel, setChannel] = useState<ContentChannel>('FACEBOOK');
  const [brandTone, setBrandTone] = useState<BrandTone>('FRESH_ENERGETIC');
  const [hook, setHook] = useState('');
  const [body, setBody] = useState('');
  const [cta, setCta] = useState('');
  const [hashtagsInput, setHashtagsInput] = useState('');
  const [productId, setProductId] = useState('');
  const [campaignId, setCampaignId] = useState('');
  const [scheduledAt, setScheduledAt] = useState('');

  const [productsList, setProductsList] = useState<Array<{ id: string; name: string }>>([]);
  const [campaignsList, setCampaignsList] = useState<Array<{ id: string; name: string }>>([]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadDependencies();
    }
  }, [isOpen]);

  const loadDependencies = async () => {
    try {
      const [prodsRes, campsRes] = await Promise.all([
        productsApi.list({ page_size: 50 }),
        campaignsApi.list({ page_size: 50 }),
      ]);
      setProductsList(prodsRes.items.map((p) => ({ id: p.id, name: p.name })));
      setCampaignsList(campsRes.items.map((c) => ({ id: c.id, name: c.name })));
    } catch {
      // Fallback
    }
  };

  useEffect(() => {
    if (item) {
      setTitle(item.title);
      setContentType(item.content_type as ContentType);
      setChannel(item.channel as ContentChannel);
      setBrandTone(item.brand_tone as BrandTone);
      setHook(item.hook || '');
      setBody(item.body);
      setCta(item.cta || '');
      setHashtagsInput(item.hashtags ? item.hashtags.join(', ') : '');
      setProductId(item.product_id || '');
      setCampaignId(item.campaign_id || '');
      setScheduledAt(item.scheduled_at ? item.scheduled_at.slice(0, 16) : '');
    } else {
      setTitle('');
      setContentType('FACEBOOK_POST');
      setChannel('FACEBOOK');
      setBrandTone('FRESH_ENERGETIC');
      setHook('');
      setBody('');
      setCta('');
      setHashtagsInput('#MocHealthy, #EatClean, #SongKhoe');
      setProductId('');
      setCampaignId('');
      setScheduledAt('');
    }
    setErrorMessage(null);
  }, [item, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setErrorMessage('Vui lòng nhập tiêu đề bài viết');
      return;
    }
    if (!body.trim()) {
      setErrorMessage('Vui lòng nhập nội dung bài viết');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    const parsedHashtags = hashtagsInput
      .split(',')
      .map((t) => t.trim())
      .filter((t) => t.length > 0)
      .map((t) => (t.startsWith('#') ? t : `#${t}`));

    try {
      if (isEditing && item) {
        const updateData: ContentUpdateInput = {
          title: title.trim(),
          content_type: contentType,
          channel,
          brand_tone: brandTone,
          hook: hook.trim() || null,
          body: body.trim(),
          cta: cta.trim() || null,
          hashtags: parsedHashtags,
          product_id: productId || null,
          campaign_id: campaignId || null,
          scheduled_at: scheduledAt ? new Date(scheduledAt).toISOString() : null,
        };
        await contentApi.update(item.id, updateData);
      } else {
        const createData: ContentCreateInput = {
          title: title.trim(),
          content_type: contentType,
          channel,
          brand_tone: brandTone,
          hook: hook.trim() || null,
          body: body.trim(),
          cta: cta.trim() || null,
          hashtags: parsedHashtags,
          product_id: productId || null,
          campaign_id: campaignId || null,
          scheduled_at: scheduledAt ? new Date(scheduledAt).toISOString() : null,
        };
        await contentApi.create(createData);
      }

      onSuccess();
      onClose();
    } catch (err: any) {
      setErrorMessage(err.message || 'Có lỗi xảy ra khi lưu bài viết');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title={isEditing ? `Chỉnh sửa bài viết: ${item?.title}` : 'Soạn thảo nội dung tiếp thị mới'}
    >
      <form onSubmit={handleSubmit} className="space-y-4 max-h-[75vh] overflow-y-auto px-1">
        {errorMessage && (
          <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg">
            {errorMessage}
          </div>
        )}

        <Input
          label="Tiêu đề nội dung *"
          placeholder="vd: Bí quyết thanh lọc cơ thể với nước ép cần tây Mộc Healthy"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <Select
            label="Kênh phân phối"
            value={channel}
            onChange={(e) => setChannel(e.target.value as ContentChannel)}
            options={AVAILABLE_CHANNELS}
          />
          <Select
            label="Định dạng bài viết"
            value={contentType}
            onChange={(e) => setContentType(e.target.value as ContentType)}
            options={AVAILABLE_TYPES}
          />
          <Select
            label="Giọng văn thương hiệu"
            value={brandTone}
            onChange={(e) => setBrandTone(e.target.value as BrandTone)}
            options={AVAILABLE_TONES}
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <Select
            label="Sản phẩm liên kết"
            value={productId}
            onChange={(e) => setProductId(e.target.value)}
            options={[
              { value: '', label: '-- Toàn bộ menu món ăn --' },
              ...productsList.map((p) => ({ value: p.id, label: p.name })),
            ]}
          />
          <Select
            label="Chiến dịch tiếp thị liên kết"
            value={campaignId}
            onChange={(e) => setCampaignId(e.target.value)}
            options={[
              { value: '', label: '-- Không thuộc chiến dịch cụ thể --' },
              ...campaignsList.map((c) => ({ value: c.id, label: c.name })),
            ]}
          />
        </div>

        <Input
          label="Hook mở đầu (Câu giật tít 3 giây đầu)"
          placeholder="vd: Bạn có biết 80% mọi người đang uống nước ép sai cách?"
          value={hook}
          onChange={(e) => setHook(e.target.value)}
        />

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Nội dung chính (Body) *
          </label>
          <textarea
            rows={5}
            value={body}
            onChange={(e) => setBody(e.target.value)}
            required
            placeholder="Viết nội dung chi tiết bài đăng hoặc kịch bản phân cảnh video tại đây..."
            className="w-full text-xs p-3 rounded-lg border border-slate-300 focus:outline-hidden focus:ring-2 focus:ring-emerald-500 font-sans"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <Input
            label="Lời kêu gọi hành động (CTA)"
            placeholder="vd: Nhấp link đặt ngay trước 10h để freeship!"
            value={cta}
            onChange={(e) => setCta(e.target.value)}
          />
          <Input
            label="Hashtags (phân cách bằng dấu phẩy)"
            placeholder="#MocHealthy, #EatClean, #Salad"
            value={hashtagsInput}
            onChange={(e) => setHashtagsInput(e.target.value)}
          />
        </div>

        <Input
          label="Thời gian lên lịch phát hành (tùy chọn)"
          type="datetime-local"
          value={scheduledAt}
          onChange={(e) => setScheduledAt(e.target.value)}
        />

        {/* Action Buttons */}
        <div className="flex justify-end gap-2 pt-3 border-t border-slate-200">
          <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting}>
            Hủy
          </Button>
          <Button type="submit" variant="primary" disabled={isSubmitting}>
            {isSubmitting ? 'Đang lưu...' : isEditing ? 'Cập nhật bài viết' : 'Lưu bản nháp'}
          </Button>
        </div>
      </form>
    </Dialog>
  );
};
