'use client';

import React, { useState } from 'react';
import {
  Dialog,
  Button,
  Select,
  Badge,
} from '@moc-healthy/ui';
import {
  MarketplaceImportPreviewResponse,
} from '@moc-healthy/contracts';
import { omnichannelApi } from '../../lib/api';

export interface MarketplaceImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportSuccess: () => void;
}

const SAMPLE_GRAB_DATA = `Order ID,Order Time,Customer Name,Phone,Address,Gross Sales,Merchant Promo,Commission,Net Payout,Items
GF-202610-101,2026-10-07 10:30,Trần Thanh Grab,0912345678,12 Lê Duẩn Q1,150000,10000,30000,110000,Nước Ép Cam Tươi x2; Salad Ức Gà x1
GF-202610-102,2026-10-07 11:15,Nguyễn Thu Hà,0987654321,45 Nguyễn Thị Minh Khai Q3,200000,0,40000,160000,Sinh Tố Bơ Healthy x2
GF-202610-103,2026-10-07 12:00,Lê Văn Tài,0933112233,88 Nam Kỳ Khởi Nghĩa,90000,5000,18000,67000,Sữa Chua Trái Cây x1`;

const SAMPLE_SHOPEE_DATA = `Shopee Order ID,Order Time,Customer,Phone,Address,Subtotal,Merchant Discount,Service Fee,Net Settlement,Items
SPF-9988-101,2026-10-07 13:00,Phạm Hùng Shopee,0901234567,100 Hai Bà Trưng Q1,180000,20000,45000,115000,Detox Rau Má x3
SPF-9988-102,2026-10-07 14:30,Đặng Bích Ngọc,0944556677,20 Pasteur Q1,240000,0,60000,180000,Combo Trái Cây 5 Màu x2`;

export const MarketplaceImportModal: React.FC<MarketplaceImportModalProps> = ({
  isOpen,
  onClose,
  onImportSuccess,
}) => {
  const [channel, setChannel] = useState<'GRAB' | 'SHOPEEFOOD' | 'MANUAL'>('GRAB');
  const [filename, setFilename] = useState('grab_merchant_report.csv');
  const [rawContent, setRawContent] = useState(SAMPLE_GRAB_DATA);

  // Preview state
  const [preview, setPreview] = useState<MarketplaceImportPreviewResponse | null>(null);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleChannelChange = (newChan: string) => {
    const ch = newChan as 'GRAB' | 'SHOPEEFOOD' | 'MANUAL';
    setChannel(ch);
    setPreview(null);
    setErrorMessage(null);
    setSuccessMessage(null);
    if (ch === 'GRAB') {
      setFilename('grab_merchant_report.csv');
      setRawContent(SAMPLE_GRAB_DATA);
    } else if (ch === 'SHOPEEFOOD') {
      setFilename('shopeefood_statement.csv');
      setRawContent(SAMPLE_SHOPEE_DATA);
    } else {
      setFilename('omnichannel_orders.csv');
      setRawContent('');
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFilename(file.name);
    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target?.result as string;
      setRawContent(text || '');
      setPreview(null);
    };
    reader.readAsText(file);
  };

  const handlePreview = async () => {
    if (!rawContent.trim()) {
      setErrorMessage('Vui lòng nhập hoặc chọn file CSV báo cáo bán hàng');
      return;
    }
    setIsLoadingPreview(true);
    setErrorMessage(null);
    try {
      const data = await omnichannelApi.previewRaw({
        channel,
        filename,
        raw_content: rawContent,
        skip_duplicates: true,
      });
      setPreview(data);
    } catch (err: any) {
      setErrorMessage(err.message || 'Lỗi khi đọc file báo cáo');
    } finally {
      setIsLoadingPreview(false);
    }
  };

  const handleExecute = async () => {
    if (!preview || preview.valid_rows === 0) {
      setErrorMessage('Không có đơn hàng hợp lệ để nhập vào hệ thống');
      return;
    }

    setIsExecuting(true);
    setErrorMessage(null);
    try {
      const res = await omnichannelApi.executeImport({
        channel,
        filename,
        raw_content: rawContent,
        skip_duplicates: true,
      });
      setSuccessMessage(
        `Đã nhập thành công ${res.imported_rows} đơn hàng từ ${channel} (Bỏ qua ${res.duplicate_rows} đơn trùng)!`
      );
      setTimeout(() => {
        onImportSuccess();
        onClose();
      }, 1200);
    } catch (err: any) {
      setErrorMessage(err.message || 'Nhập dữ liệu thất bại');
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="Nhập Báo Cáo Đơn Hàng Đa Kênh (GrabFood / ShopeeFood)"
      description="Tự động bóc tách doanh thu gộp, phí hoa hồng sàn (20-25%), khuyến mãi quán và doanh thu thực nhận (Net Settlement)"
      maxWidth="xl"
      footer={
        <>
          <Button variant="outline" size="sm" onClick={onClose} disabled={isExecuting}>
            Đóng
          </Button>
          {!preview ? (
            <Button
              variant="primary"
              size="sm"
              onClick={handlePreview}
              isLoading={isLoadingPreview}
            >
              🔍 Xem trước dữ liệu (Preview)
            </Button>
          ) : (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPreview(null)}
                disabled={isExecuting}
              >
                ← Tải file khác
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleExecute}
                isLoading={isExecuting}
                disabled={preview.valid_rows === 0}
              >
                ✓ Xác nhận nhập {preview.valid_rows} đơn vào hệ thống
              </Button>
            </div>
          )}
        </>
      }
    >
      <div className="space-y-4 text-xs text-slate-700 max-h-[75vh] overflow-y-auto pr-1">
        {errorMessage && (
          <div className="p-3 bg-red-50 text-red-700 rounded-lg border border-red-200">
            {errorMessage}
          </div>
        )}
        {successMessage && (
          <div className="p-3 bg-emerald-50 text-emerald-800 rounded-lg border border-emerald-200">
            {successMessage}
          </div>
        )}

        {!preview ? (
          <>
            {/* Step 1: Chọn kênh và nạp dữ liệu */}
            <div className="p-4 bg-slate-50/70 rounded-xl border border-slate-200/80 space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 items-end">
                <Select
                  label="Chọn sàn đối tác *"
                  value={channel}
                  onChange={(e) => handleChannelChange(e.target.value)}
                  options={[
                    { value: 'GRAB', label: '🛵 GrabFood Merchant' },
                    { value: 'SHOPEEFOOD', label: '🛍️ ShopeeFood Partner' },
                    { value: 'MANUAL', label: '📄 File CSV đa kênh khác' },
                  ]}
                />
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Tải file từ máy tính (.csv, .txt)
                  </label>
                  <input
                    type="file"
                    accept=".csv,.txt"
                    onChange={handleFileUpload}
                    className="text-xs text-slate-500 file:mr-2 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100"
                  />
                </div>
              </div>

              <div className="flex items-center justify-between pt-1">
                <span className="text-[11px] text-slate-500">
                  Tập tin hiện tại: <strong className="text-slate-800">{filename}</strong>
                </span>
                <button
                  type="button"
                  onClick={() => handleChannelChange(channel)}
                  className="text-emerald-700 font-semibold hover:underline text-[11px]"
                >
                  ↺ Nạp lại mẫu demo {channel}
                </button>
              </div>
            </div>

            {/* Nội dung file preview */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-800 block">
                Nội dung báo cáo (CSV Text)
              </label>
              <textarea
                rows={8}
                value={rawContent}
                onChange={(e) => setRawContent(e.target.value)}
                placeholder="Dán nội dung CSV xuất từ cổng merchant của Grab hoặc ShopeeFood..."
                className="w-full text-[11px] font-mono p-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
              />
              <p className="text-[11px] text-slate-400">
                Hệ thống tự động nhận diện các cột mã đơn, doanh thu món, khuyến mãi quán, và phí dịch vụ chiết khấu của sàn.
              </p>
            </div>
          </>
        ) : (
          <>
            {/* Step 2: Kết quả Preview & Tính toán */}
            <div className="p-4 bg-emerald-50/60 rounded-xl border border-emerald-200/80 space-y-3">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div>
                  <h4 className="font-bold text-emerald-950 text-sm">
                    Xem trước kết quả phân tích: {preview.channel}
                  </h4>
                  <p className="text-[11px] text-emerald-700">
                    Tập tin: {preview.filename} | Tổng số dòng: {preview.total_rows}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Badge variant="success" size="sm">
                    {preview.valid_rows} đơn hợp lệ
                  </Badge>
                  {preview.duplicate_rows > 0 && (
                    <Badge variant="warning" size="sm">
                      {preview.duplicate_rows} đơn trùng (bỏ qua)
                    </Badge>
                  )}
                </div>
              </div>

              {/* Financial Breakdown Table */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-emerald-200/60 text-center">
                <div className="p-2 bg-white rounded-lg border border-emerald-100">
                  <span className="text-[10px] text-slate-400 block uppercase font-bold">Doanh thu gộp (Gross)</span>
                  <span className="font-black text-slate-800 text-xs">
                    {preview.gross_amount_total.toLocaleString('vi-VN')}đ
                  </span>
                </div>
                <div className="p-2 bg-white rounded-lg border border-emerald-100">
                  <span className="text-[10px] text-slate-400 block uppercase font-bold">Phí sàn (Platform Fee)</span>
                  <span className="font-black text-rose-600 text-xs">
                    -{preview.platform_fee_total.toLocaleString('vi-VN')}đ
                  </span>
                </div>
                <div className="p-2 bg-white rounded-lg border border-emerald-100">
                  <span className="text-[10px] text-slate-400 block uppercase font-bold">Khuyến mãi quán</span>
                  <span className="font-black text-amber-600 text-xs">
                    -{preview.merchant_discount_total.toLocaleString('vi-VN')}đ
                  </span>
                </div>
                <div className="p-2 bg-white rounded-lg border border-emerald-200 shadow-xs">
                  <span className="text-[10px] text-emerald-800 block uppercase font-bold">Thực nhận (Net Settlement)</span>
                  <span className="font-black text-emerald-700 text-sm">
                    {preview.net_settlement_total.toLocaleString('vi-VN')}đ
                  </span>
                </div>
              </div>
            </div>

            {/* List of Orders Preview */}
            <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
              <div className="px-4 py-2.5 bg-slate-50 border-b border-slate-200 font-bold text-[11px] text-slate-700 grid grid-cols-12 gap-2">
                <span className="col-span-3">Mã đơn & Thời gian</span>
                <span className="col-span-3">Khách hàng</span>
                <span className="col-span-2 text-right">Doanh thu gộp</span>
                <span className="col-span-2 text-right">Phí sàn</span>
                <span className="col-span-2 text-right">Thực nhận</span>
              </div>
              <div className="divide-y divide-slate-100 max-h-56 overflow-y-auto">
                {preview.preview_items.map((it) => (
                  <div
                    key={it.row_index}
                    className={`px-4 py-2 text-[11px] grid grid-cols-12 gap-2 items-center ${
                      it.is_duplicate ? 'bg-amber-50/40 text-slate-400' : 'hover:bg-slate-50/60'
                    }`}
                  >
                    <div className="col-span-3">
                      <span className="font-mono font-bold text-slate-900 block truncate">
                        {it.external_order_id}
                      </span>
                      <span className="text-[10px] text-slate-400">{it.ordered_at}</span>
                      {it.is_duplicate && (
                        <span className="text-[10px] text-amber-600 font-semibold block">⚠️ Đã tồn tại</span>
                      )}
                    </div>
                    <div className="col-span-3 truncate">
                      <span className="font-medium text-slate-800 block truncate">{it.customer_name}</span>
                      <span className="text-[10px] text-slate-400 font-mono">{it.customer_phone}</span>
                    </div>
                    <div className="col-span-2 text-right font-medium">
                      {it.gross_amount.toLocaleString('vi-VN')}đ
                    </div>
                    <div className="col-span-2 text-right text-rose-600 font-medium">
                      -{it.platform_fee.toLocaleString('vi-VN')}đ
                    </div>
                    <div className="col-span-2 text-right font-bold text-emerald-700">
                      {it.net_amount.toLocaleString('vi-VN')}đ
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </Dialog>
  );
};
