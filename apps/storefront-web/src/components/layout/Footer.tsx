import React from 'react';
import Link from 'next/link';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-900 text-slate-300 pt-14 pb-24 md:pb-14 border-t border-slate-800 text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        {/* Cam kết thương hiệu */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pb-10 border-b border-slate-800 text-slate-400">
          <div className="flex items-start space-x-3.5">
            <span className="text-2xl p-2.5 rounded-xl bg-emerald-950/60 text-emerald-400 border border-emerald-800/40 shrink-0">
              🥑
            </span>
            <div>
              <h4 className="font-bold text-white text-sm mb-1">100% Trái Cây Tươi Tuyển Chọn</h4>
              <p className="leading-relaxed">
                Nguồn gốc rõ ràng từ các nhà vườn chuẩn VietGAP, Đà Lạt và nhập khẩu loại 1, bảo quản lạnh tối ưu.
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-3.5">
            <span className="text-2xl p-2.5 rounded-xl bg-emerald-950/60 text-emerald-400 border border-emerald-800/40 shrink-0">
              🍃
            </span>
            <div>
              <h4 className="font-bold text-white text-sm mb-1">Thuần Khiết & Tự Nhiên</h4>
              <p className="leading-relaxed">
                Cam kết không chất bảo quản, không phẩm màu nhân tạo, không siro hóa chất độc hại.
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-3.5">
            <span className="text-2xl p-2.5 rounded-xl bg-emerald-950/60 text-emerald-400 border border-emerald-800/40 shrink-0">
              ⚡
            </span>
            <div>
              <h4 className="font-bold text-white text-sm mb-1">Giao Nhanh Trong 30 Phút</h4>
              <p className="leading-relaxed">
                Đóng gói chuyên dụng giữ nhiệt và giao ngay sau khi sơ chế, đảm bảo độ giòn ngọt mọng nước.
              </p>
            </div>
          </div>
        </div>

        {/* Thông tin chi tiết */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Cột 1: Thương hiệu */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-xl bg-emerald-600 flex items-center justify-center text-white font-extrabold text-base">
                M
              </div>
              <span className="text-base font-extrabold text-white">Mộc Healthy</span>
            </div>
            <p className="text-slate-400 leading-relaxed">
              Sứ mệnh mang năng lượng xanh lành mạnh từ trái cây tươi, nước ép nguyên bản đến từng bữa ăn và bàn làm việc của bạn.
            </p>
            <div className="text-[11px] text-slate-500">
              Giấy chứng nhận VSATTP số 123/2026/ATTP-BKH
            </div>
          </div>

          {/* Cột 2: Danh mục chính */}
          <div className="space-y-3">
            <h5 className="font-bold text-white uppercase tracking-wider text-[11px]">Thực Đơn Healthy</h5>
            <ul className="space-y-2 text-slate-400">
              <li>
                <Link href="/categories/trai-cay-tuoi" className="hover:text-emerald-400 transition">
                  Trái Cây Tươi Cắt Sẵn
                </Link>
              </li>
              <li>
                <Link href="/categories/nuoc-ep-nguyen-chat" className="hover:text-emerald-400 transition">
                  Nước Ép Ép Chậm 100%
                </Link>
              </li>
              <li>
                <Link href="/categories/sinh-to-do-uong-da-xay" className="hover:text-emerald-400 transition">
                  Sinh Tố Trái Cây & Bơ
                </Link>
              </li>
              <li>
                <Link href="/categories/sua-chua-hoa-qua" className="hover:text-emerald-400 transition">
                  Sữa Chua Men Sống Hoa Quả
                </Link>
              </li>
              <li>
                <Link href="/categories/tra-matcha-thanh-nhiet" className="hover:text-emerald-400 transition">
                  Trà Trái Cây & Matcha
                </Link>
              </li>
            </ul>
          </div>

          {/* Cột 3: Hỗ trợ & Chính sách */}
          <div className="space-y-3">
            <h5 className="font-bold text-white uppercase tracking-wider text-[11px]">Chăm Sóc Khách Hàng</h5>
            <ul className="space-y-2 text-slate-400">
              <li>
                <Link href="/tracking" className="hover:text-emerald-400 transition text-emerald-400 font-semibold">
                  🔍 Tra cứu tình trạng đơn hàng
                </Link>
              </li>
              <li>
                <span className="hover:text-emerald-400 cursor-pointer">
                  Chính sách đổi trả trong 2h
                </span>
              </li>
              <li>
                <span className="hover:text-emerald-400 cursor-pointer">
                  Chính sách giao hàng & Freeship
                </span>
              </li>
              <li>
                <span className="hover:text-emerald-400 cursor-pointer">
                  Cam kết bảo mật thông tin
                </span>
              </li>
              <li>
                <Link href="/promotions" className="hover:text-emerald-400 transition">
                  Quy chế mã Voucher & Khuyến mãi
                </Link>
              </li>
            </ul>
          </div>

          {/* Cột 4: Liên hệ */}
          <div className="space-y-3">
            <h5 className="font-bold text-white uppercase tracking-wider text-[11px]">Liên Hệ Đặt Hàng</h5>
            <div className="space-y-2 text-slate-400">
              <p>📍 Bếp Trung Tâm Mộc Healthy, TP. Hồ Chí Minh</p>
              <p>
                📞 Hotline:{' '}
                <a href="tel:0901234567" className="text-emerald-400 font-bold hover:underline">
                  0901 234 567
                </a>
              </p>
              <p>✉️ Email: lienhe@mochealthy.vn</p>
              <p>⏰ 07:00 - 21:30 (Thứ 2 - Chủ Nhật)</p>
            </div>
          </div>
        </div>

        {/* Bản quyền */}
        <div className="pt-8 border-t border-slate-800 text-center text-slate-500 text-[11px]">
          © {new Date().getFullYear()} Mộc Healthy Platform. All rights reserved. Omnichannel AI Commerce.
        </div>
      </div>
    </footer>
  );
};
