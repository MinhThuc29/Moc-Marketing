# Prompt: Thiết kế lại nhận diện giao diện storefront Mộc Healthy

> Paste toàn bộ phần dưới vào một phiên Claude Code mới, chạy tại thư mục gốc repo.

---

Dùng skill `frontend-design` cho toàn bộ việc này. Đọc skill trước khi lập kế hoạch.

## Việc cần làm

Thiết kế lại ngôn ngữ thị giác của `apps/storefront-web` — không phải sửa vặt từng chỗ, mà xây một hệ thống màu + chữ + nhịp có logic, rồi áp dụng lại lên các trang hiện có. Giữ nguyên toàn bộ chức năng, route, API, và kiểu dữ liệu.

## Brief

- **Sản phẩm:** Mộc Healthy — trái cây tuyển chọn cắt sẵn, nước ép 100% nguyên chất, sinh tố, sữa chua hoa quả. Đặt online, giao trong 30 phút.
- **Khách hàng:** nhân viên văn phòng Việt Nam 24–40 tuổi, đặt trên điện thoại, trong giờ làm, thường là bữa phụ hoặc bữa trưa nhẹ. Họ quyết định trong vài chục giây.
- **Việc chính của trang:** làm cho người ta tin đồ này *tươi hôm nay* và đặt được trong dưới 60 giây.
- **Vấn đề hiện tại:** trang trông như template SaaS được tô màu xanh lá. Không có cảm giác thực phẩm tươi, không có cá tính, không phân biệt được với bất kỳ shop healthy nào khác.

Trước khi thiết kế, hãy tự xác định và nói ra: chất liệu, kết cấu, màu sắc thật của thế giới trái cây cắt sẵn ở Việt Nam trông như thế nào — và rút hướng thị giác ra từ đó, không phải từ thư viện mẫu e-commerce.

## Hiện trạng đã khảo sát (dữ liệu thật, đừng khảo sát lại từ đầu)

Toàn bộ 5 dấu hiệu "thiết kế mặc định" đều có mặt:

1. **Gradient trang trí vô cớ** — 9 chỗ ở storefront: `src/app/page.tsx:46,100,237`, `src/components/layout/Header.tsx:49`, `src/components/ProductCard.tsx:64`, `src/app/cart/page.tsx:114`, `src/app/categories/[slug]/page.tsx:82`, `src/app/order-success/page.tsx:85`. Riêng `src/components/PromoBannerCarousel.tsx:47` dùng gradient tím `from-purple-50 to-indigo-50/50` làm màu mặc định cho loại khuyến mãi "còn lại" — tím không mang nghĩa gì.
2. **Card đồng dạng** — 19/33 khối card dùng chung đúng một vỏ: `rounded-3xl` + `border-slate-200/80` + `shadow-sm`, bất kể nội dung là card sản phẩm, hộp tổng tiền hay chú thích phụ. Không có thứ bậc thị giác.
3. **Nhãn ALL-CAPS cỡ nhỏ** — 35 chỗ, mẫu gần như y hệt: `text-[10px]`/`text-xs` + `font-extrabold` + `uppercase` + `tracking-wider`. Dùng cho eyebrow section, tiêu đề cột footer, tên danh mục trên card, tiêu đề khối trong giỏ hàng. Riêng với tiếng Việt, viết hoa toàn bộ ở cỡ 10–11px làm dấu bị cắt và chồng — đây là lỗi đọc được, không chỉ lỗi thẩm mỹ.
4. **Emoji làm icon** — 130 emoji trong 19 file, và đây *là* hệ icon: `package.json` không có thư viện icon nào, cả codebase chỉ có 3 thẻ `<svg>`. 🥑 xuất hiện 19 lần. `src/components/ProductCard.tsx:67` còn dùng `getFallbackEmoji()` làm ảnh sản phẩm khi thiếu thumbnail.
5. **"→" gắn đuôi CTA** — `src/app/page.tsx:149,171,217`, `src/app/promotions/page.tsx:175`, `src/components/HealthyTipsSection.tsx:74`.

**Về màu — đây là gốc của vấn đề "không có tương quan":**

Đếm số lần dùng class màu ở storefront: `slate` 380, `emerald` 336, `rose` 21, `red` 19, `purple` 7, `amber` 7, `teal` 6, `orange` 1, `indigo` 1.

Nghĩa là: emerald bị dùng cho *mọi thứ* — thương hiệu, link, trạng thái thành công, nhãn danh mục, nút chính, badge, nền section, viền hover. Khi một màu mang mọi nghĩa thì nó không còn mang nghĩa nào. Còn purple/indigo/orange xuất hiện 1–7 lần như những màu mồ côi, không thuộc hệ nào.

Không có token màu nào cả: `src/app/globals.css` chỉ khai báo `--background: #ffffff` và `--foreground: #1e293b`, phần còn lại là màu Tailwind rải thẳng trong JSX. Font là system stack mặc định, chưa chọn typeface nào.

## Yêu cầu riêng về màu (phần người đặt hàng quan tâm nhất)

Kết quả phải là một **hệ màu có vai trò**, không phải một bảng màu đẹp. Cụ thể:

- 5–6 màu nền tảng, mỗi màu có tên và mã hex, mỗi màu có **đúng một vai trò** được ghi rõ. Các vai trò cần tách bạch: màu thương hiệu / màu nền & giấy / màu chữ (không dùng đen tuyệt đối, cũng không dùng đen pha tím kiểu `#0B0B0B`) / một màu nhấn duy nhất để gọi hành động / các màu trạng thái (thành công, cảnh báo, lỗi).
- **Màu thương hiệu và màu nút chính phải khác nhau.** Hiện tại cả hai đều là emerald, nên nút không nổi lên khỏi nền thương hiệu.
- Màu trạng thái không được trùng màu thương hiệu. Nếu "thành công" và "thương hiệu" cùng là xanh lá thì người dùng không đọc được tín hiệu.
- Các màu phải có quan hệ giải thích được — cùng gốc sắc độ, hoặc bổ túc có chủ đích, hoặc rút từ màu thật của nguyên liệu. Viết ra quan hệ đó bằng một câu. Nếu không giải thích được tại sao màu B đứng cạnh màu A, thì chưa phải hệ.
- Kiểm tra tương phản WCAG AA cho mọi cặp chữ/nền và báo số đo thật. Chữ tiếng Việt có dấu cần tương phản tốt hơn mức tối thiểu.
- Xoá hoặc đưa vào hệ toàn bộ màu mồ côi (purple, indigo, orange).
- Màu phải sống được cạnh ảnh sản phẩm thật — ảnh trái cây đã rất rực, nên giao diện không được tranh màu với ảnh.

## Ràng buộc kỹ thuật

- Next.js 15 (App Router), React 19, TailwindCSS 3.4.17, `tailwind.config.ts` đã có sẵn.
- Token màu khai báo ở `tailwind.config.ts` (`theme.extend.colors`) + biến CSS trong `src/app/globals.css`, đặt tên **theo vai trò** (`brand`, `surface`, `ink`, `accent`, `success`…), không đặt theo màu (`green-600`).
- Font: chọn typeface có bộ dấu tiếng Việt đầy đủ và kiểm chứng điều đó trước khi dùng. Nạp qua `next/font`. Tối đa 2 họ chữ.
- Thay emoji bằng hệ icon SVG thật: dựng component `<Icon>` dùng chung. Nếu cần thêm dependency, hỏi trước khi cài.
- Không đổi props công khai của component hiện có nếu không cần thiết; nếu có đổi, cập nhật hết nơi gọi.
- Không đụng `apps/admin-web` và `apps/api` trong lượt này.

## Những thứ bị cấm

Ngoài danh sách trong skill, với dự án này cấm thêm:

- Gradient dùng làm trang trí. Gradient chỉ được phép khi nó *mang thông tin* (ví dụ lớp phủ để chữ đọc được trên ảnh).
- Chữ viết hoa toàn bộ ở cỡ dưới 14px. Với tiếng Việt, tránh ALL-CAPS ở mọi cỡ trừ khi có lý do rõ.
- Eyebrow label phía trên tiêu đề section khi nó chỉ lặp lại tiêu đề.
- Một bán kính bo góc duy nhất cho mọi thứ. Bán kính phải phản ánh thứ bậc.
- Shadow giống nhau dưới mọi khối. Phần lớn khối không cần shadow.
- "→" nối đuôi chữ trên nút và link.
- Emoji trong giao diện.
- Hiệu ứng fade-and-slide-up khi cuộn tới từng section, và hover transition trên mọi card.

## Cách làm — hai pha, dừng lại giữa chừng

**Pha 1 — kế hoạch, chưa viết code.** Trình bày:

1. Hướng thị giác: 2–3 câu, rút ra từ chất liệu thật của sản phẩm, nói rõ trang này sẽ *cảm giác* như cái gì.
2. Bảng token màu: tên, hex, vai trò, lý do màu đó thuộc hệ, số đo tương phản.
3. Chữ: tên typeface, vai trò từng họ, thang cỡ chữ kèm line-height, và ghi chú riêng cho dấu tiếng Việt.
4. Bố cục: mô tả bằng văn xuôi + wireframe ASCII cho trang chủ và cho card sản phẩm. Nói rõ căn lề trái/giữa và vì sao.
5. Hero: đề xuất cụ thể trang chủ mở đầu bằng cái gì, và vì sao đó là thứ đặc trưng nhất của Mộc Healthy. "Số lớn + nhãn nhỏ + gradient" là lựa chọn mặc định — nếu định dùng thì phải chứng minh nó thực sự tốt nhất.
6. Chỗ duy nhất được phép táo bạo: chọn một yếu tố làm điểm nhớ, mọi thứ còn lại phải im lặng.

Rồi **tự soát kế hoạch đó**: với mỗi mục, tự hỏi nếu nhận một brief shop healthy bất kỳ thì có ra đúng kết quả này không. Chỗ nào có, sửa lại và nói rõ đã đổi gì, vì sao.

**Dừng ở đây. Trình bày kế hoạch và đợi duyệt.** Không viết code trước khi được duyệt.

**Pha 2 — dựng, sau khi duyệt.** Thứ tự:

1. Token màu + font + thang chữ vào `tailwind.config.ts` và `globals.css`.
2. Component `<Icon>` và thay toàn bộ emoji — bao gồm `getFallbackEmoji()` trong `ProductCard.tsx`.
3. `ProductCard` và `Header` trước (xuất hiện ở mọi trang), rồi trang chủ, rồi lần lượt: danh mục, chi tiết sản phẩm, giỏ hàng, thanh toán, khuyến mãi, tra cứu đơn, đặt hàng thành công, 404.
4. Mỗi bước: chạy build kiểm tra, và tự phê bình — khối nào còn đang trang trí mà không mang thông tin thì bỏ đi.

Sàn chất lượng, không cần nhắc lại trong báo cáo nhưng phải có: chạy tốt từ 360px, focus bàn phím nhìn thấy rõ, tôn trọng `prefers-reduced-motion`, tương phản đạt AA, vùng chạm tối thiểu 44px trên mobile.

Cuối cùng, liệt kê những gì đã đổi và những gì cố ý giữ nguyên.
