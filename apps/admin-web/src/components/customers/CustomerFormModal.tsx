'use client';

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  Button,
  Input,
  Select,
} from '@moc-healthy/ui';
import { CustomerListItem } from '@moc-healthy/contracts';
import { customersApi } from '../../lib/api';

export interface CustomerFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  customer?: CustomerListItem | null;
  onSuccess: () => void;
}

export const CustomerFormModal: React.FC<CustomerFormModalProps> = ({
  isOpen,
  onClose,
  customer,
  onSuccess,
}) => {
  const isEditing = !!customer;

  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [defaultAddress, setDefaultAddress] = useState('');
  const [source, setSource] = useState('ONLINE');
  const [tagsInput, setTagsInput] = useState('');
  const [notes, setNotes] = useState('');
  const [consentMarketing, setConsentMarketing] = useState(true);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (customer) {
      setFullName(customer.full_name);
      setPhone(customer.phone);
      setEmail(customer.email || '');
      setDefaultAddress(customer.default_address || '');
      setSource(customer.source || 'ONLINE');
      setTagsInput(customer.tags ? customer.tags.join(', ') : '');
      setConsentMarketing(true);
      setNotes('');
    } else {
      setFullName('');
      setPhone('');
      setEmail('');
      setDefaultAddress('');
      setSource('ONLINE');
      setTagsInput('');
      setNotes('');
      setConsentMarketing(true);
    }
    setErrorMessage(null);
  }, [customer, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName.trim() || (!isEditing && !phone.trim())) {
      setErrorMessage('Vui lòng điền đầy đủ họ tên và số điện thoại');
      return;
    }

    const tags = tagsInput
      .split(',')
      .map((t) => t.trim())
      .filter((t) => t.length > 0);

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      if (isEditing && customer) {
        await customersApi.update(customer.id, {
          full_name: fullName.trim(),
          email: email.trim() || undefined,
          default_address: defaultAddress.trim() || undefined,
          tags,
          notes: notes.trim() || undefined,
          consent_marketing: consentMarketing,
        });
      } else {
        await customersApi.create({
          full_name: fullName.trim(),
          phone: phone.trim(),
          email: email.trim() || undefined,
          default_address: defaultAddress.trim() || undefined,
          source,
          tags,
          notes: notes.trim() || undefined,
          consent_marketing: consentMarketing,
        });
      }

      onSuccess();
      onClose();
    } catch (err: any) {
      setErrorMessage(err.message || 'Lỗi khi lưu thông tin khách hàng');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title={isEditing ? '✏️ Cập nhật thông tin khách hàng' : '➕ Thêm mới hồ sơ khách hàng'}
      maxWidth="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4 text-xs text-slate-700">
        {errorMessage && (
          <div className="p-2.5 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg">
            {errorMessage}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Họ và tên khách hàng <span className="text-rose-500">*</span>
            </label>
            <Input
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Ví dụ: Nguyễn Văn An"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Số điện thoại <span className="text-rose-500">*</span>
            </label>
            <Input
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="0912345678"
              disabled={isEditing}
              required
            />
            {isEditing && (
              <p className="text-[10px] text-slate-400 mt-0.5">
                Số điện thoại là định danh chính, không thể thay đổi
              </p>
            )}
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Địa chỉ Email
            </label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="an.nguyen@gmail.com"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Kênh tiếp cận ban đầu
            </label>
            <Select
              value={source}
              onChange={(e) => setSource(e.target.value)}
              options={[
                { value: 'ONLINE', label: '🌐 Website Online' },
                { value: 'WALK_IN', label: '🏪 Mua tại quầy' },
                { value: 'HOTLINE', label: '📞 Hotline đặt bàn' },
                { value: 'GRAB', label: '🛵 GrabFood' },
                { value: 'SHOPEEFOOD', label: '🟠 ShopeeFood' },
                { value: 'ZALO', label: '💬 Zalo OA' },
              ]}
              disabled={isEditing}
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Địa chỉ giao hàng mặc định
          </label>
          <Input
            value={defaultAddress}
            onChange={(e) => setDefaultAddress(e.target.value)}
            placeholder="Số nhà, tên đường, phường/xã, quận/huyện..."
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Nhãn sở thích (Tags phân khúc, cách nhau bằng dấu phẩy)
          </label>
          <Input
            value={tagsInput}
            onChange={(e) => setTagsInput(e.target.value)}
            placeholder="thich_salad, gym_member, an_chay, van_phong"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Ghi chú nội bộ về khách hàng (Dị ứng, khẩu vị, lưu ý giao hàng)
          </label>
          <Input
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Ví dụ: Thích ít ngọt, không hành tây, gọi trước khi giao"
          />
        </div>

        <div className="flex items-center gap-2 pt-1">
          <input
            type="checkbox"
            id="consent_mkt"
            checked={consentMarketing}
            onChange={(e) => setConsentMarketing(e.target.checked)}
            className="rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
          />
          <label htmlFor="consent_mkt" className="text-xs text-slate-600 select-none cursor-pointer">
            Khách hàng đồng ý nhận tin nhắn khuyến mãi & chăm sóc qua SMS / Zalo OA
          </label>
        </div>

        <div className="flex justify-end gap-2 pt-3 border-t border-slate-200">
          <Button type="button" variant="outline" size="sm" onClick={onClose} disabled={isSubmitting}>
            Hủy
          </Button>
          <Button type="submit" variant="primary" size="sm" disabled={isSubmitting}>
            {isSubmitting ? 'Đang lưu...' : isEditing ? 'Cập nhật' : 'Tạo hồ sơ'}
          </Button>
        </div>
      </form>
    </Dialog>
  );
};
