'use client';

import React, { useState } from 'react';
import { Dialog, Button, Input, Badge } from '@moc-healthy/ui';
import { Category } from '@moc-healthy/contracts';
import { categoriesApi } from '../../lib/api';

interface CategoryManagerDialogProps {
  isOpen: boolean;
  onClose: () => void;
  categories: Category[];
  onRefresh: () => void;
  canWrite: boolean;
}

export const CategoryManagerDialog: React.FC<CategoryManagerDialogProps> = ({
  isOpen,
  onClose,
  categories,
  onRefresh,
  canWrite,
}) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [description, setDescription] = useState('');
  const [sortOrder, setSortOrder] = useState('0');
  const [active, setActive] = useState(true);

  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const resetForm = () => {
    setEditingId(null);
    setName('');
    setSlug('');
    setDescription('');
    setSortOrder('0');
    setActive(true);
    setErrorMessage(null);
  };

  const startEdit = (cat: Category) => {
    setEditingId(cat.id);
    setName(cat.name);
    setSlug(cat.slug);
    setDescription(cat.description || '');
    setSortOrder(String(cat.sort_order));
    setActive(cat.active);
    setErrorMessage(null);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setErrorMessage('Vui lòng nhập tên danh mục');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    try {
      const payload = {
        name: name.trim(),
        slug: slug.trim() || undefined,
        description: description.trim() || undefined,
        sort_order: parseInt(sortOrder) || 0,
        active,
      };

      if (editingId) {
        await categoriesApi.update(editingId, payload);
      } else {
        await categoriesApi.create(payload);
      }

      resetForm();
      onRefresh();
    } catch (err: any) {
      setErrorMessage(err.message || 'Lỗi khi lưu danh mục');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (cat: Category) => {
    if (!window.confirm(`Bạn có chắc muốn xóa danh mục "${cat.name}"? Các sản phẩm thuộc danh mục này sẽ chuyển về chưa phân loại.`)) {
      return;
    }

    try {
      await categoriesApi.delete(cat.id);
      if (editingId === cat.id) resetForm();
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Lỗi khi xóa danh mục');
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="Quản lý Danh mục F&B"
      maxWidth="xl"
      footer={
        <Button variant="secondary" onClick={onClose}>
          Đóng
        </Button>
      }
    >
      <div className="space-y-6">
        {errorMessage && (
          <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg border border-red-200">
            {errorMessage}
          </div>
        )}

        {/* Form add / edit */}
        {canWrite && (
          <form
            onSubmit={handleSave}
            className="p-4 bg-slate-50 border border-slate-200/80 rounded-xl space-y-3"
          >
            <div className="flex justify-between items-center">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                {editingId ? 'Chỉnh sửa danh mục' : 'Thêm danh mục mới'}
              </h4>
              {editingId && (
                <button
                  type="button"
                  onClick={resetForm}
                  className="text-xs text-slate-500 hover:text-slate-800 underline"
                >
                  Hủy sửa
                </button>
              )}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <Input
                  label="Tên danh mục *"
                  placeholder="VD: Trái cây sấy dẻo"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>
              <div>
                <Input
                  label="Slug URL (tùy chọn)"
                  placeholder="VD: trai-cay-say-deo"
                  value={slug}
                  onChange={(e) => setSlug(e.target.value)}
                />
              </div>
              <div>
                <Input
                  label="Thứ tự hiển thị"
                  type="number"
                  value={sortOrder}
                  onChange={(e) => setSortOrder(e.target.value)}
                />
              </div>
              <div className="md:col-span-2">
                <Input
                  label="Mô tả danh mục"
                  placeholder="Mô tả ngắn gọn..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>
              <div className="flex items-center pt-6">
                <label className="flex items-center gap-2 cursor-pointer text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={active}
                    onChange={(e) => setActive(e.target.checked)}
                    className="w-4 h-4 text-emerald-600 rounded"
                  />
                  <span>Kích hoạt hiển thị</span>
                </label>
              </div>
            </div>
            <div className="flex justify-end pt-2">
              <Button variant="primary" size="sm" type="submit" isLoading={isLoading}>
                {editingId ? 'Lưu cập nhật' : '+ Thêm danh mục'}
              </Button>
            </div>
          </form>
        )}

        {/* Category list */}
        <div className="overflow-x-auto border border-slate-200 rounded-lg">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase">
              <tr>
                <th className="px-4 py-3 w-16">Thứ tự</th>
                <th className="px-4 py-3">Tên danh mục</th>
                <th className="px-4 py-3">Slug</th>
                <th className="px-4 py-3">Trạng thái</th>
                {canWrite && <th className="px-4 py-3 text-right">Thao tác</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {categories.map((cat) => (
                <tr key={cat.id} className="hover:bg-slate-50/50">
                  <td className="px-4 py-3 font-mono text-xs text-slate-500">{cat.sort_order}</td>
                  <td className="px-4 py-3 font-medium text-slate-900">{cat.name}</td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-500">{cat.slug}</td>
                  <td className="px-4 py-3">
                    {cat.active ? (
                      <Badge variant="success">Hoạt động</Badge>
                    ) : (
                      <Badge variant="neutral">Ẩn</Badge>
                    )}
                  </td>
                  {canWrite && (
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => startEdit(cat)}
                          className="text-xs text-emerald-600 hover:text-emerald-800 font-medium"
                        >
                          Sửa
                        </button>
                        <span className="text-slate-300">|</span>
                        <button
                          type="button"
                          onClick={() => handleDelete(cat)}
                          className="text-xs text-red-600 hover:text-red-800 font-medium"
                        >
                          Xóa
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Dialog>
  );
};
