from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.product import Product
from app.models.campaign import Campaign
from app.models.content import (
    ContentType,
    ContentChannel,
    BrandTone,
)
from app.schemas.content import (
    AIGenerateRequest,
    AIGeneratedVariant,
    AIGenerateResponse,
)


def format_vnd(amount: float) -> str:
    return f"{int(amount):,}đ".replace(",", ".")


class AIContentService:
    @staticmethod
    async def generate_content(
        db: AsyncSession,
        req: AIGenerateRequest,
    ) -> AIGenerateResponse:
        # 1. Fetch Product context if provided
        product: Optional[Product] = None
        if req.product_id:
            res = await db.execute(select(Product).where(Product.id == req.product_id))
            product = res.scalar_one_or_none()

        # 2. Fetch Campaign context if provided
        campaign: Optional[Campaign] = None
        if req.campaign_id:
            res = await db.execute(select(Campaign).where(Campaign.id == req.campaign_id))
            campaign = res.scalar_one_or_none()

        prod_name = product.name if product else "Set Món Healthy Tuyển Chọn"
        prod_price_str = format_vnd(float(product.sale_price or product.base_price)) if product else "Giá ưu đãi hôm nay"
        shelf_life = product.shelf_life if (product and product.shelf_life) else "3-5 ngày bảo quản lạnh mát"
        ingredients = product.ingredients if (product and product.ingredients) else "Nguyên liệu tươi sạch 100% tự nhiên không chất bảo quản"

        camp_name = campaign.name if campaign else "Ưu Đãi Đặc Biệt Mộc Healthy"
        camp_code = campaign.code if campaign else "MOCHEALTHY"
        landing_page = campaign.landing_page if (campaign and campaign.landing_page) else "https://mochanh.vn"

        # 3. Tone context
        tone_map = {
            "FRESH_ENERGETIC": "Tươi mới, truyền cảm hứng sống khỏe, năng lượng tràn đầy",
            "NUTRITION_EXPERT": "Chuyên gia dinh dưỡng, minh bạch thành phần, khoa học & đáng tin cậy",
            "WARM_FRIENDLY": "Ấm áp, thấu hiểu, chăm sóc như người thân trong gia đình",
            "MINIMAL_HEALTHY": "Thanh lọc cơ thể, phong cách sống xanh tinh tế, tối giản calo",
            "TRENDY_HUMOR": "Bắt trend hài hước, hóm hỉnh, hợp gu giới trẻ và dân văn phòng",
        }
        tone_desc = tone_map.get(req.brand_tone, "Chân thực, gần gũi")

        # 4. Generate variants according to channel & content type
        variants: List[AIGeneratedVariant] = []

        if req.content_type in (ContentType.TIKTOK_SCRIPT.value, ContentType.REEL_SCRIPT.value):
            # Video Short Scripts
            variants.append(
                AIGeneratedVariant(
                    title=f"[TikTok 45s] Giải cứu bữa trưa công sở với {prod_name}",
                    hook="POV: Bạn chỉ có 15 phút nghỉ trưa nhưng không muốn nạp đồ ăn dầu mỡ độc hại? Đừng lướt vội!",
                    body=(
                        "👉 Phân cảnh 1 (0-3s): Quay cận cảnh hộp đồ ăn nhanh ngấy mỡ đối lập với nắp hộp Mộc Healthy mở ra tươi rói.\n"
                        f"👉 Phân cảnh 2 (4-15s): Cận cảnh từng thành phần: {ingredients}. Calo vừa đủ, no lâu mà không bị đầy bụng.\n"
                        f"👉 Phân cảnh 3 (16-30s): Ăn thử miếng đầu tiên giòn tan, âm thanh ASMR tự nhiên. Bảo quản tươi ngon {shelf_life}.\n"
                        f"👉 Phân cảnh 4 (31-45s): Giá chỉ {prod_price_str}. Đặt liền tay trước 10h30 để được giao ngay giờ ăn trưa!"
                    ),
                    cta=f"Nhấp ngay vào link bên dưới giỏ hàng để nhận voucher {camp_code} hôm nay!",
                    hashtags=["#MocHealthy", "#EatCleanVietNam", "#BuaTruaCongSo", "#HealthyFood", "#ASMRFood"],
                    storyboard_suggestion="Ánh sáng tự nhiên góc 45 độ, âm nhạc lofi vui tươi, voice-over giọng nữ trẻ trung dứt khoát.",
                    rationale="Mô hình PAS (Problem-Agitate-Solution) đánh trúng insight thiếu thời gian của dân văn phòng, chuyển đổi cao qua hình ảnh thực tế.",
                )
            )
            variants.append(
                AIGeneratedVariant(
                    title=f"[Reel 30s] 3 Lý do bạn nên đổi sang {prod_name} ngay hôm nay",
                    hook="Đừng ăn kiêng khổ sở nữa! Đây là món giúp mình giữ dáng mà không hề bị đói lả.",
                    body=(
                        f"1️⃣ 100% nguyên liệu tự nhiên ({ingredients}), nói KHÔNG với đường hóa học.\n"
                        f"2️⃣ Tiết kiệm 45 phút nấu nướng mỗi ngày - chỉ cần mở hộp là thưởng thức ngay.\n"
                        f"3️⃣ Chi phí hợp lý: chỉ {prod_price_str} cho một bữa ăn chuẩn dinh dưỡng."
                    ),
                    cta="Bình luận 'HEALTHY' hoặc bấm vào bio để Mộc gửi thực đơn tuần cho bạn nhé!",
                    hashtags=["#GiuDangKhoaHoc", "#MocHealthyMenu", "#AnSachSongKhoe", "#TrendingFood"],
                    storyboard_suggestion="Text on screen to rõ ràng, hiệu ứng chuyển cảnh nhanh bắt mắt theo nhịp beat sôi động.",
                    rationale="Định dạng Listicle (3 lý do) có tỷ lệ retention xem hết video cao nhất trên Reels và TikTok.",
                )
            )
        elif req.channel == ContentChannel.ZALO.value:
            # Zalo OA / ZNS Messages
            variants.append(
                AIGeneratedVariant(
                    title=f"[Zalo OA] Nhắc lịch bổ sung dinh dưỡng cùng {prod_name}",
                    hook=f"🌿 Mộc Healthy gửi tặng bạn ưu đãi bữa ăn xanh hôm nay!",
                    body=(
                        f"Chào bạn, một ngày làm việc bận rộn đừng quên chăm sóc bản thân nhé.\n\n"
                        f"Hôm nay Mộc gợi ý món {prod_name} vừa cập bến bếp:\n"
                        f"• Thành phần: {ingredients}\n"
                        f"• Hạn sử dụng: {shelf_life}\n"
                        f"• Ưu đãi chiến dịch: Chỉ {prod_price_str}\n\n"
                        f"Đơn hàng được chuẩn bị tươi mới và giao tận bàn làm việc trong 30-45 phút."
                    ),
                    cta=f"👉 Bấm để chọn món và áp mã {camp_code}: {landing_page}",
                    hashtags=["#MocHealthyZalo", "#ChamSocKhachHang"],
                    storyboard_suggestion="Kèm ảnh banner vuông 800x800 chụp cận cảnh món ăn màu sắc tươi tắn.",
                    rationale="Ngắn gọn, trang trọng, thân thiện chuẩn phong cách Zalo OA CSKH giúp tăng tỷ lệ mở tin và click link.",
                )
            )
            variants.append(
                AIGeneratedVariant(
                    title=f"[Zalo ZNS Flash] Ưu đãi đặc quyền thành viên Mộc Healthy",
                    hook=f"⚡ Flash Sale thành viên: Giảm trực tiếp cho {prod_name}!",
                    body=(
                        f"Gửi riêng đến bạn yêu mến lối sống lành mạnh,\n\n"
                        f"Chỉ duy nhất trong đợt {camp_name}, {prod_name} được trợ giá đặc biệt còn {prod_price_str}.\n"
                        f"Số lượng chuẩn bị có hạn trong ngày để đảm bảo độ tươi ngon cao nhất."
                    ),
                    cta=f"Đặt ngay kẻo lỡ: {landing_page}",
                    hashtags=["#MocHealthyFlashSale", "#MemberExclusive"],
                    storyboard_suggestion="Thiết kế thẻ ZNS mẫu thông báo dịch vụ chuẩn của Zalo.",
                    rationale="Tạo cảm giác khan hiếm và đặc quyền riêng cho tệp khách hàng quen thuộc.",
                )
            )
        else:
            # Facebook Post & Instagram Post
            variants.append(
                AIGeneratedVariant(
                    title=f"[Facebook/Insta] Khởi động ngày mới tràn đầy năng lượng cùng {prod_name}",
                    hook=f"Cơ thể bạn xứng đáng nhận những gì tươi sạch nhất mỗi ngày 🌱",
                    body=(
                        f"Giữa nhịp sống hối hả, một bữa ăn cân bằng không chỉ giúp bạn no bụng, mà còn là lời nhắc yêu thương bản thân đúng cách.\n\n"
                        f"Mộc Healthy tự hào mang đến {prod_name} với cam kết 3 KHÔNG:\n"
                        f"❌ Không chất bảo quản tổng hợp\n"
                        f"❌ Không đường tinh luyện độc hại\n"
                        f"❌ Không nguyên liệu đông lạnh qua ngày\n\n"
                        f"✨ Từng phần ăn được chế biến từ: {ingredients}. Giữ trọn vitamin và khoáng chất tự nhiên.\n"
                        f"💰 Mức giá thân thiện: {prod_price_str} ({shelf_life})."
                    ),
                    cta=f"👉 Đặt ngay tại {landing_page} hoặc nhắn tin trực tiếp cho Mộc để được tư vấn lộ trình ăn sạch nhé!",
                    hashtags=["#MocHealthy", "#EatClean", "#SongKhoeMoiNgay", "#ThucPhamSach", "#HealthyLifestyle"],
                    storyboard_suggestion="Album 4 ảnh: 1 ảnh hero toàn cảnh, 2 ảnh cận cảnh nguyên liệu xanh, 1 ảnh bao bì đóng hộp kraft thân thiện môi trường.",
                    rationale="Tiếp cận theo mô hình AIDA (Attention - Interest - Desire - Action), củng cố niềm tin về an toàn vệ sinh thực phẩm.",
                )
            )
            variants.append(
                AIGeneratedVariant(
                    title=f"[Facebook/Insta] Bí quyết giữ vòng eo thon gọn không cần nhịn ăn",
                    hook=f"Bạn có biết: 80% kết quả vóc dáng đến từ căn bếp của bạn?",
                    body=(
                        f"Ăn sạch (Eat Clean) không đồng nghĩa với ăn uống nhạt nhẽo và kham khổ.\n\n"
                        f"Với {prod_name}, mỗi bữa ăn là một trải nghiệm thưởng thức trọn vẹn:\n"
                        f"🥗 Hương vị đậm đà tự nhiên từ gia vị thảo mộc\n"
                        f"🥑 Cân đối hoàn hảo Protein - Tinh bột tốt - Chất béo lành mạnh\n"
                        f"⚡ Giúp bạn no lâu, duy trì sự tỉnh táo làm việc suốt cả buổi chiều\n\n"
                        f"Đặc biệt trong chiến dịch {camp_name}: Giá ưu đãi chỉ {prod_price_str}."
                    ),
                    cta=f"Nhắn tin ngay cho Fanpage hoặc ghé {landing_page} để Mộc chuẩn bị bữa ăn nóng hổi cho bạn!",
                    hashtags=["#MocHealthy", "#GiuDangTuNhien", "#BuaAnDinhDuong", "#SaladTuoi", "#NuocEpDetox"],
                    storyboard_suggestion="Ảnh carousel so sánh lượng calo và bảng dinh dưỡng minh bạch.",
                    rationale="Đánh vào nhu cầu giữ dáng, làm đẹp nhưng vẫn muốn ăn ngon miệng của đối tượng khách hàng nữ 22-40 tuổi.",
                )
            )

        # Slice to requested number of variants
        chosen_variants = variants[:req.num_variants]

        prompt_summary = (
            f"F&B Healthy Food Copywriter Engine | Product: {prod_name} | Campaign: {camp_name} "
            f"| Channel: {req.channel} | Type: {req.content_type} | Tone: {tone_desc}"
        )
        if req.custom_instruction:
            prompt_summary += f" | Custom Note: {req.custom_instruction}"

        return AIGenerateResponse(
            variants=chosen_variants,
            prompt_used=prompt_summary,
            model_name="MocHealthy-AI-Copywriter-v2.1",
            product_name=prod_name,
            campaign_name=camp_name,
        )
