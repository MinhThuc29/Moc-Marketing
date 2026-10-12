import React from 'react';

const REVIEWS = [
  {
    name: 'Phương Linh (Quận 1)',
    avatar: '👩‍💼',
    rating: 5,
    tag: 'Táo New Zealand & Nước ép cam',
    comment:
      'Táo cắt sẵn đóng hộp rất sạch, giòn ngọt và không hề bị thâm đen. Nước ép cam nguyên chất 100% không gắt cổ. Giao hàng chỉ tầm 25 phút là tới văn phòng.',
    time: '2 ngày trước',
  },
  {
    name: 'Thanh Tuấn (Bình Thạnh)',
    avatar: '👨‍💻',
    rating: 5,
    tag: 'Sinh tố bơ sáp & Sữa chua dâu',
    comment:
      'Sinh tố bơ cực kỳ béo ngậy, ngọt thanh đúng chuẩn ít đường healthy. Sữa chua dâu men sống cho cả nhà ăn tráng miệng ai cũng khen. 10 điểm chất lượng!',
    time: '3 ngày trước',
  },
  {
    name: 'Bích Ngọc (Quận 3)',
    avatar: '👩‍🎨',
    rating: 5,
    tag: 'Nước ép cần tây táo xanh',
    comment:
      'Nước ép cần tây thơm ngon dễ uống hơn mình tưởng rất nhiều nhờ có vị thanh của táo xanh. Đóng chai kín đáo, tem mác HSD rõ ràng rất an tâm.',
    time: '1 tuần trước',
  },
];

export const ReviewsSection: React.FC = () => {
  return (
    <section className="bg-emerald-950 text-white rounded-3xl p-6 sm:p-10 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-2 border-b border-emerald-900 pb-4">
        <div>
          <span className="text-emerald-400 font-extrabold text-xs uppercase tracking-wider block mb-1">
            ⭐️ Đánh Giá Khách Hàng
          </span>
          <h2 className="text-xl sm:text-2xl font-black tracking-tight">
            Hơn 10.000+ Khách Hàng Yêu Thích Mộc Healthy
          </h2>
        </div>
        <div className="flex items-center space-x-2 text-sm text-emerald-300">
          <span className="font-extrabold text-white text-lg">4.9 / 5.0</span>
          <span>(1.850+ đánh giá xác thực)</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {REVIEWS.map((r, idx) => (
          <div
            key={idx}
            className="bg-emerald-900/40 border border-emerald-800/60 p-5 rounded-2xl flex flex-col justify-between space-y-3 backdrop-blur-xs"
          >
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2.5">
                  <span className="text-2xl p-1 bg-emerald-800/50 rounded-xl">{r.avatar}</span>
                  <div>
                    <h4 className="font-bold text-white text-xs sm:text-sm">{r.name}</h4>
                    <span className="text-[10px] text-emerald-400 block">{r.tag}</span>
                  </div>
                </div>
                <div className="text-amber-400 text-xs">{'★'.repeat(r.rating)}</div>
              </div>

              <p className="text-xs text-emerald-100/90 leading-relaxed italic">
                "{r.comment}"
              </p>
            </div>

            <div className="text-[10px] text-emerald-400 text-right pt-2 border-t border-emerald-800/40">
              {r.time}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};
