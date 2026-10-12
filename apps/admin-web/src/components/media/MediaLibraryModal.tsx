'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Dialog, Button, Input, Skeleton, EmptyState, Badge } from '@moc-healthy/ui';
import { MediaAsset } from '@moc-healthy/contracts';
import { mediaApi } from '../../lib/api';

interface MediaLibraryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect?: (media: MediaAsset) => void;
  folder?: string;
}

export const MediaLibraryModal: React.FC<MediaLibraryModalProps> = ({
  isOpen,
  onClose,
  onSelect,
  folder = 'products',
}) => {
  const [mediaList, setMediaList] = useState<MediaAsset[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [uploadTags, setUploadTags] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successNotice, setSuccessNotice] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadMedia = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const res = await mediaApi.list({
        q: searchTerm.trim() || undefined,
        folder,
        page: 1,
        page_size: 48,
      });
      setMediaList(res.items);
    } catch (err: any) {
      setErrorMessage(err.message || 'Không thể tải danh sách tệp media');
    } finally {
      setIsLoading(false);
    }
  }, [searchTerm, folder]);

  useEffect(() => {
    if (isOpen) {
      loadMedia();
      setSuccessNotice(null);
    }
  }, [isOpen, loadMedia]);

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    setIsUploading(true);
    setErrorMessage(null);
    setSuccessNotice(null);

    try {
      const fileArray = Array.from(files);
      const uploaded = await mediaApi.upload(fileArray, folder, uploadTags);
      setSuccessNotice(`Đã tải lên thành công ${uploaded.length} tệp media!`);
      loadMedia();
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Lỗi tải tệp lên');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (asset: MediaAsset) => {
    if (!window.confirm(`Bạn có chắc muốn xóa tệp "${asset.original_name}"?`)) {
      return;
    }

    try {
      await mediaApi.delete(asset.id);
      setMediaList((prev) => prev.filter((item) => item.id !== asset.id));
      setSuccessNotice('Đã xóa tệp media thành công.');
    } catch (err: any) {
      alert(err.message || 'Lỗi khi xóa tệp');
    }
  };

  const handleCopyUrl = (url: string) => {
    const fullUrl = url.startsWith('http') ? url : `${window.location.origin}${url}`;
    navigator.clipboard.writeText(fullUrl);
    setSuccessNotice('Đã sao chép đường dẫn ảnh vào bộ nhớ tạm!');
    setTimeout(() => setSuccessNotice(null), 3000);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="Thư viện Media & Tải lên tệp (Media Library)"
      maxWidth="xl"
      footer={
        <Button variant="secondary" onClick={onClose}>
          Đóng
        </Button>
      }
    >
      <div className="space-y-4">
        {/* Notices */}
        {errorMessage && (
          <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg border border-red-200">
            {errorMessage}
          </div>
        )}
        {successNotice && (
          <div className="p-3 bg-emerald-50 text-emerald-800 text-sm rounded-lg border border-emerald-200 flex items-center justify-between">
            <span>✅ {successNotice}</span>
            <button
              onClick={() => setSuccessNotice(null)}
              className="text-xs text-emerald-700 underline"
            >
              Đóng
            </button>
          </div>
        )}

        {/* 1. Upload Dropzone Area */}
        <div className="p-4 border-2 border-dashed border-emerald-300 bg-emerald-50/40 rounded-xl transition hover:border-emerald-500">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-2xl shrink-0">
                ☁️
              </div>
              <div>
                <h4 className="text-sm font-bold text-slate-800">
                  Tải lên hình ảnh hoặc video
                </h4>
                <p className="text-xs text-slate-500">
                  Kéo thả tệp hoặc chọn từ máy tính (Hỗ trợ JPG, PNG, WEBP, GIF, SVG, MP4 — tối đa 20MB)
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept="image/*,video/*"
                className="hidden"
                onChange={(e) => handleFileUpload(e.target.files)}
                disabled={isUploading}
              />
              <Button
                variant="primary"
                size="sm"
                isLoading={isUploading}
                onClick={() => fileInputRef.current?.click()}
              >
                + Chọn tệp tải lên
              </Button>
            </div>
          </div>
        </div>

        {/* 2. Search & Toolbar */}
        <div className="flex items-center justify-between gap-3 pt-2">
          <div className="flex-1 max-w-sm">
            <Input
              placeholder="Tìm kiếm tệp theo tên hoặc tags..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <Button variant="ghost" size="sm" onClick={loadMedia} isLoading={isLoading}>
            🔄 Làm mới
          </Button>
        </div>

        {/* 3. Media Grid */}
        {isLoading ? (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 py-4">
            {[1, 2, 3, 4, 5, 6, 7, 8].map((n) => (
              <Skeleton key={n} height="140px" />
            ))}
          </div>
        ) : mediaList.length === 0 ? (
          <EmptyState
            title="Chưa có tệp media nào"
            description="Tải lên hình ảnh đầu tiên của bạn để sử dụng cho sản phẩm hoặc bài đăng tiếp thị."
            icon="🖼️"
            actionText="+ Tải tệp lên"
            onAction={() => fileInputRef.current?.click()}
          />
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 max-h-[440px] overflow-y-auto pr-1">
            {mediaList.map((item) => {
              const isImage = item.mime_type.startsWith('image/');

              return (
                <div
                  key={item.id}
                  className="group relative bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs hover:shadow-md hover:border-emerald-500 transition flex flex-col justify-between"
                >
                  {/* Thumbnail container */}
                  <div className="aspect-square bg-slate-100 relative overflow-hidden flex items-center justify-center">
                    {isImage ? (
                      <img
                        src={item.thumbnail_url || item.url}
                        alt={item.original_name}
                        className="w-full h-full object-cover group-hover:scale-105 transition duration-200"
                        onError={(e) => {
                          (e.target as HTMLElement).style.display = 'none';
                        }}
                      />
                    ) : (
                      <div className="text-3xl">🎥</div>
                    )}

                    {/* Overlay Action Buttons on Hover */}
                    <div className="absolute inset-0 bg-slate-900/60 opacity-0 group-hover:opacity-100 transition flex items-center justify-center gap-2 p-2">
                      {onSelect && (
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => {
                            onSelect(item);
                            onClose();
                          }}
                        >
                          Chọn
                        </Button>
                      )}
                      <button
                        type="button"
                        onClick={() => handleCopyUrl(item.url)}
                        className="p-1.5 rounded-lg bg-white/90 text-slate-700 hover:bg-white text-xs font-semibold"
                        title="Sao chép URL"
                      >
                        🔗
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(item)}
                        className="p-1.5 rounded-lg bg-red-600 text-white hover:bg-red-700 text-xs font-semibold"
                        title="Xóa tệp"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>

                  {/* Metadata Info */}
                  <div className="p-2.5 bg-white border-t border-slate-100">
                    <p
                      className="text-xs font-semibold text-slate-800 truncate"
                      title={item.original_name}
                    >
                      {item.original_name}
                    </p>
                    <div className="flex items-center justify-between text-[10px] text-slate-400 mt-0.5">
                      <span>{formatFileSize(item.file_size)}</span>
                      {item.width && item.height && (
                        <span>
                          {item.width}×{item.height}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Dialog>
  );
};
