import React from 'react';
import { Button } from './Button';

export interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  className?: string;
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  onPageChange,
  className = '',
}) => {
  if (totalPages <= 1) return null;

  return (
    <div className={`flex items-center justify-between px-4 py-3 bg-white border-t border-slate-100 sm:px-6 ${className}`}>
      <div className="flex justify-between flex-1 sm:hidden">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1}
        >
          Trang trước
        </Button>
        <span className="text-xs text-slate-500 self-center">
          {currentPage} / {totalPages}
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
        >
          Trang sau
        </Button>
      </div>

      <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
        <div>
          <p className="text-xs text-slate-600">
            Hiển thị trang <span className="font-semibold text-slate-900">{currentPage}</span> trên tổng số{' '}
            <span className="font-semibold text-slate-900">{totalPages}</span> trang
          </p>
        </div>
        <div>
          <nav className="inline-flex gap-1 -space-x-px rounded-md shadow-xs" aria-label="Pagination">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage <= 1}
            >
              ← Trước
            </Button>
            <span className="px-3 py-1.5 text-xs font-semibold text-slate-700 bg-slate-50 rounded-lg flex items-center border border-slate-200">
              {currentPage}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage >= totalPages}
            >
              Sau →
            </Button>
          </nav>
        </div>
      </div>
    </div>
  );
};
