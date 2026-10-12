import React from 'react';
import Link from 'next/link';

const TIPS = [
  {
    tag: 'Detox & Đề kháng',
    title: 'Bắt đầu ngày mới năng lượng với Nước ép Cần Tây & Táo Xanh',
    desc: 'Cần tây chứa apigenin và luteolin giúp chống viêm tự nhiên, kết hợp táo xanh giàu vitamin C tạo nên ly nước ép thanh lọc cơ thể sảng khoái.',
    time: '5 phút đọc',
    icon: '🌱',
    link: '/categories/nuoc-ep-nguyen-chat',
  },
  {
    tag: 'Tiêu hóa khỏe',
    title: 'Tại sao nên bổ sung Sữa Chua Men Sống Hoa Quả vào bữa xế?',
    desc: 'Hàng tỷ lợi khuẩn probiotics sống giúp cân bằng hệ vi sinh đường ruột, hỗ trợ hấp thu dinh dưỡng và kiểm soát cảm giác thèm ngọt hiệu quả.',
    time: '4 phút đọc',
    icon: '🥛',
    link: '/categories/sua-chua-hoa-qua',
  },
  {
    tag: 'Dinh dưỡng chuẩn',
    title: 'Chất béo lành mạnh từ Trái Bơ Sáp Đắk Lắk nguyên bản',
    desc: 'Bơ sáp chứa axit béo không bão hòa đơn (MUFA) bảo vệ tim mạch, kết hợp sữa hạt dinh dưỡng tạo nên bữa phụ no lâu và tốt cho làn da.',
    time: '6 phút đọc',
    icon: '🥑',
    link: '/categories/sinh-to-do-uong-da-xay',
  },
];

export const HealthyTipsSection: React.FC = () => {
  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <span className="text-emerald-700 font-extrabold text-xs uppercase tracking-wider block">
            🥗 Cẩm Nang Sống Khỏe
          </span>
          <h2 className="text-lg sm:text-xl font-bold text-slate-900 tracking-tight">
            Mẹo Dinh Dưỡng & Năng Lượng Từ Mộc
          </h2>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {TIPS.map((tip, idx) => (
          <div
            key={idx}
            className="bg-white p-5 rounded-2xl border border-slate-200/80 hover:border-emerald-300 hover:shadow-md transition-all flex flex-col justify-between space-y-3"
          >
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="bg-emerald-50 text-emerald-800 font-bold px-2 py-0.5 rounded-full text-[10px]">
                  {tip.tag}
                </span>
                <span className="text-slate-400 text-[11px]">{tip.time}</span>
              </div>

              <h3 className="font-bold text-slate-800 text-sm hover:text-emerald-700 transition leading-snug">
                {tip.title}
              </h3>

              <p className="text-xs text-slate-500 leading-relaxed line-clamp-3">
                {tip.desc}
              </p>
            </div>

            <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
              <Link
                href={tip.link}
                className="font-bold text-emerald-700 hover:underline inline-flex items-center gap-1"
              >
                <span>Xem thực đơn</span>
                <span>→</span>
              </Link>
              <span className="text-xl">{tip.icon}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};
