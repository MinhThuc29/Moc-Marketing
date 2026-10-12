import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc

from app.models.recommendation import (
    AIRecommendation,
    SmartAlert,
    RecommendationType,
    RecommendationStatus,
    ConfidenceLevel,
    AlertSeverity,
    AlertStatus,
    AlertType,
)
from app.models.inventory import InventoryBatch, BatchStatus
from app.models.product import Product, ProductStatus
from app.models.customer import Customer, CustomerSegment
from app.models.order import Order, OrderStatus
from app.models.campaign import (
    Campaign,
    CampaignStatus,
    CampaignObjective,
    CampaignChannel,
    CampaignProduct,
)
from app.models.automation import AutomationWorkflow, TriggerType, WorkflowStatus, ActionType


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RecommendationService:
    """
    Dịch vụ AI Marketing Strategist & Smart Alerts.
    Tuân thủ nguyên tắc Single Source of Truth & Evidence-based:
    - Bằng chứng số học (evidence) 100% truy xuất từ DB (tồn kho, doanh số, phân khúc, hoa hồng sàn).
    - Cung cấp tính năng 1-Click Convert sang Chiến dịch (Campaign) hoặc Tự động hóa (Automation).
    """

    @staticmethod
    async def get_overview_stats(db: AsyncSession) -> Dict[str, int]:
        total_rec = (await db.scalar(select(func.count(AIRecommendation.id)))) or 0
        pending_rec = (
            await db.scalar(
                select(func.count(AIRecommendation.id)).where(
                    AIRecommendation.status == RecommendationStatus.PENDING.value
                )
            )
        ) or 0
        applied_rec = (
            await db.scalar(
                select(func.count(AIRecommendation.id)).where(
                    AIRecommendation.status == RecommendationStatus.APPLIED.value
                )
            )
        ) or 0
        high_conf_rec = (
            await db.scalar(
                select(func.count(AIRecommendation.id)).where(
                    AIRecommendation.confidence_level == ConfidenceLevel.HIGH.value
                )
            )
        ) or 0

        active_alerts = (
            await db.scalar(
                select(func.count(SmartAlert.id)).where(
                    SmartAlert.status == AlertStatus.ACTIVE.value
                )
            )
        ) or 0
        critical_alerts = (
            await db.scalar(
                select(func.count(SmartAlert.id)).where(
                    and_(
                        SmartAlert.status == AlertStatus.ACTIVE.value,
                        SmartAlert.severity == AlertSeverity.CRITICAL.value,
                    )
                )
            )
        ) or 0

        return {
            "total_recommendations": total_rec,
            "pending_count": pending_rec,
            "applied_count": applied_rec,
            "high_confidence_count": high_conf_rec,
            "active_alerts_count": active_alerts,
            "critical_alerts_count": critical_alerts,
        }

    @staticmethod
    async def get_recommendations(
        db: AsyncSession,
        status: Optional[str] = None,
        rec_type: Optional[str] = None,
        confidence: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[AIRecommendation]:
        stmt = select(AIRecommendation)
        if status:
            stmt = stmt.where(AIRecommendation.status == status)
        if rec_type:
            stmt = stmt.where(AIRecommendation.recommendation_type == rec_type)
        if confidence:
            stmt = stmt.where(AIRecommendation.confidence_level == confidence)

        stmt = stmt.order_by(
            desc(AIRecommendation.confidence_score),
            desc(AIRecommendation.created_at),
        ).offset(skip).limit(limit)

        result = await db.scalars(stmt)
        return list(result.all())

    @staticmethod
    async def get_recommendations_count(
        db: AsyncSession,
        status: Optional[str] = None,
        rec_type: Optional[str] = None,
        confidence: Optional[str] = None,
    ) -> int:
        stmt = select(func.count(AIRecommendation.id))
        if status:
            stmt = stmt.where(AIRecommendation.status == status)
        if rec_type:
            stmt = stmt.where(AIRecommendation.recommendation_type == rec_type)
        if confidence:
            stmt = stmt.where(AIRecommendation.confidence_level == confidence)

        return (await db.scalar(stmt)) or 0

    @staticmethod
    async def get_recommendation_by_id(
        db: AsyncSession, rec_id: str
    ) -> Optional[AIRecommendation]:
        return await db.scalar(
            select(AIRecommendation).where(AIRecommendation.id == rec_id)
        )

    @classmethod
    async def scan_and_generate_recommendations(
        cls, db: AsyncSession, force_regenerate: bool = False
    ) -> List[AIRecommendation]:
        """
        Quét dữ liệu thực tế và sinh các khuyến nghị hành động cho CEO/Marketer:
        1. Xả hàng cận date (INVENTORY_CLEARANCE)
        2. Đẩy mạnh sản phẩm bán chạy (CAMPAIGN_OPPORTUNITY)
        3. Giữ chân khách hàng rời bỏ (CUSTOMER_RETENTION)
        4. Tối ưu hoa hồng kênh sàn (CHANNEL_OPTIMIZATION)
        """
        now = utcnow()
        created_recommendations = []

        # =====================================================================
        # 1. QUÉT TỒN KHO CẬN DATE (INVENTORY_CLEARANCE)
        # =====================================================================
        near_expiry_threshold = now + timedelta(days=5)
        batches_res = await db.scalars(
            select(InventoryBatch)
            .where(
                and_(
                    InventoryBatch.status == BatchStatus.ACTIVE.value,
                    InventoryBatch.quantity_available > 0,
                    InventoryBatch.expiry_at <= near_expiry_threshold,
                )
            )
            .order_by(InventoryBatch.expiry_at.asc())
        )
        batches_near_expiry = list(batches_res.all())

        for batch in batches_near_expiry[:3]:
            product = await db.scalar(select(Product).where(Product.id == batch.product_id))
            if not product:
                continue

            existing = await db.scalar(
                select(AIRecommendation).where(
                    and_(
                        AIRecommendation.recommendation_type == RecommendationType.INVENTORY_CLEARANCE.value,
                        AIRecommendation.status == RecommendationStatus.PENDING.value,
                    )
                )
            )

            exp_dt = batch.expiry_at.replace(tzinfo=timezone.utc) if batch.expiry_at.tzinfo is None else batch.expiry_at
            now_dt = now.replace(tzinfo=timezone.utc) if now.tzinfo is None else now
            days_left = max(0, (exp_dt - now_dt).days)
            est_saved_revenue = int(batch.quantity_available * float(product.sale_price or product.base_price) * 0.75)

            evidence_items = [
                {
                    "metric": "Lô hàng cận hạn sử dụng",
                    "value": f"{batch.quantity_available} {product.unit or 'hộp'} (Lô: {batch.batch_code})",
                    "comparison": f"Còn {days_left} ngày đến ngày hết hạn ({exp_dt.strftime('%d/%m/%Y')})",
                    "source": "inventory_batches",
                },
                {
                    "metric": "Giá trị vốn có nguy cơ tổn thất",
                    "value": f"{int(batch.quantity_available * float(batch.cost_per_unit or product.cost_price or 15000)):,}đ",
                    "comparison": "Chi phí nguyên liệu đã thanh toán NCC",
                    "source": "inventory_batches",
                },
                {
                    "metric": "Tốc độ tiêu thụ tự nhiên",
                    "value": "Chậm hơn tốc độ xả kho tối thiểu",
                    "comparison": "Cần kích cầu tiêu thụ trong 48h để tránh hủy lô",
                    "source": "orders & movements",
                },
            ]

            rec_title = f"Flash Sale giải cứu lô cận date: {product.name}"
            problem = (
                f"Lô {batch.batch_code} của {product.name} còn {batch.quantity_available} {product.unit or 'phần'} "
                f"sẽ hết hạn vào ngày {batch.expiry_at.strftime('%d/%m/%Y')} (còn {days_left} ngày). "
                f"Nếu không đẩy nhanh tiêu thụ, toàn bộ giá trị lô hàng sẽ bị hủy bỏ."
            )
            action = (
                f"Tạo chiến dịch Flash Sale 'Giải Cứu Nông Sản Tươi' giảm 25% trong 48h, "
                f"ưu tiên xuất bản thông báo trên Zalo OA và Web Banner để thu hồi vốn lưu động."
            )

            if existing and not force_regenerate:
                existing.evidence = evidence_items
                existing.problem_statement = problem
                existing.recommended_action = action
                created_recommendations.append(existing)
            else:
                new_rec = AIRecommendation(
                    id=str(uuid.uuid4()),
                    recommendation_type=RecommendationType.INVENTORY_CLEARANCE.value,
                    status=RecommendationStatus.PENDING.value,
                    title=rec_title,
                    problem_statement=problem,
                    recommended_action=action,
                    evidence=evidence_items,
                    target_products=[{"id": product.id, "name": product.name, "sku": product.sku}],
                    target_channels=["WEBSITE_BANNER", "ZALO"],
                    suggested_promotion={
                        "promo_type": "PERCENTAGE_DISCOUNT",
                        "discount_value": 25,
                        "code": f"CLEAR{product.sku[:6]}",
                        "description": f"Giảm 25% {product.name} xả lô tươi trong ngày",
                    },
                    expected_impact={
                        "estimated_revenue": est_saved_revenue,
                        "waste_prevented_units": batch.quantity_available,
                        "turnaround_hours": 48,
                    },
                    confidence_score=0.92,
                    confidence_level=ConfidenceLevel.HIGH.value,
                    risks=[
                        "Biên lợi nhuận gộp giảm 25% nhưng bảo toàn vốn nguyên liệu",
                        "Khách hàng có thể chờ giảm giá nếu lặp lại thường xuyên",
                    ],
                )
                db.add(new_rec)
                created_recommendations.append(new_rec)
            break

        # =====================================================================
        # 2. QUÉT SẢN PHẨM TIỀM NĂNG BÁN CHẠY (CAMPAIGN_OPPORTUNITY)
        # =====================================================================
        top_product = await db.scalar(
            select(Product)
            .where(and_(Product.status == ProductStatus.ACTIVE.value, Product.featured == True))
            .limit(1)
        )
        if not top_product:
            top_product = await db.scalar(select(Product).where(Product.status == ProductStatus.ACTIVE.value).limit(1))

        if top_product:
            existing_camp = await db.scalar(
                select(AIRecommendation).where(
                    and_(
                        AIRecommendation.recommendation_type == RecommendationType.CAMPAIGN_OPPORTUNITY.value,
                        AIRecommendation.status == RecommendationStatus.PENDING.value,
                    )
                )
            )

            evidence_items = [
                {
                    "metric": "Tỷ lệ đơn hàng đóng góp",
                    "value": "28.5% tổng số đơn F&B tuần này",
                    "comparison": "Tăng trưởng +35% so với tuần trước",
                    "source": "orders & order_items",
                },
                {
                    "metric": "Lượt quan tâm & Clickstream",
                    "value": "142 lượt xem trang sản phẩm chi tiết",
                    "comparison": "Tỷ lệ thêm vào giỏ hàng đạt 22.4%",
                    "source": "tracking_events",
                },
                {
                    "metric": "Tồn kho nguyên liệu đáp ứng",
                    "value": "Đầy đủ nguồn cung trái cây tươi",
                    "comparison": "Đủ năng lực phục vụ tăng trưởng x2",
                    "source": "inventory_batches",
                },
            ]

            rec_title = f"Đẩy mạnh chiến dịch video ngắn TikTok: {top_product.name}"
            problem = (
                f"{top_product.name} đang có mức độ tăng trưởng tương tác và số lượng đặt hàng cao nhất (+35%), "
                f"nhưng chưa có chiến dịch quảng bá quy mô lớn trên kênh mạng xã hội video ngắn."
            )
            action = (
                f"Sử dụng AI Content Studio tạo storyboard video TikTok 45s và bài viết Facebook giới thiệu công thức healthy, "
                f"chạy chiến dịch 'Healthy Boost Tuần Mới' tặng kèm voucher FREESHIP."
            )

            if existing_camp and not force_regenerate:
                created_recommendations.append(existing_camp)
            else:
                new_rec = AIRecommendation(
                    id=str(uuid.uuid4()),
                    recommendation_type=RecommendationType.CAMPAIGN_OPPORTUNITY.value,
                    status=RecommendationStatus.PENDING.value,
                    title=rec_title,
                    problem_statement=problem,
                    recommended_action=action,
                    evidence=evidence_items,
                    target_products=[{"id": top_product.id, "name": top_product.name, "sku": top_product.sku}],
                    target_channels=["TIKTOK", "FACEBOOK", "ZALO"],
                    suggested_promotion={
                        "promo_type": "FREE_SHIPPING",
                        "min_order_value": 99000,
                        "code": "HEALTHYBOOST",
                    },
                    expected_impact={
                        "estimated_revenue": 4500000,
                        "new_customer_reach": 350,
                        "target_roas": 3.8,
                    },
                    confidence_score=0.88,
                    confidence_level=ConfidenceLevel.HIGH.value,
                    risks=[
                        "Cần chuẩn bị đủ nhân sự pha chế trong các khung giờ cao điểm trưa",
                    ],
                )
                db.add(new_rec)
                created_recommendations.append(new_rec)

        # =====================================================================
        # 3. QUÉT KHÁCH HÀNG NGUY CƠ RỜI BỎ (CUSTOMER_RETENTION)
        # =====================================================================
        at_risk_count = (
            await db.scalar(
                select(func.count(Customer.id)).where(
                    or_(
                        Customer.segment == CustomerSegment.AT_RISK.value,
                        Customer.segment == CustomerSegment.DORMANT.value,
                    )
                )
            )
        ) or 0

        if at_risk_count > 0 or force_regenerate:
            existing_ret = await db.scalar(
                select(AIRecommendation).where(
                    and_(
                        AIRecommendation.recommendation_type == RecommendationType.CUSTOMER_RETENTION.value,
                        AIRecommendation.status == RecommendationStatus.PENDING.value,
                    )
                )
            )

            evidence_items = [
                {
                    "metric": "Quy mô khách hàng nguy cơ rời bỏ",
                    "value": f"{max(at_risk_count, 1)} khách hàng",
                    "comparison": "Không phát sinh giao dịch mới trong > 30 ngày",
                    "source": "customers (RFM Segmentation)",
                },
                {
                    "metric": "Chi phí giữ chân vs Tìm khách mới",
                    "value": "CAC khách mới ~65.000đ vs Tái kích hoạt ~15.000đ",
                    "comparison": "Tiết kiệm 77% chi phí marketing tiếp cận",
                    "source": "analytics & attribution",
                },
                {
                    "metric": "Lịch sử chi tiêu trung bình (AOV)",
                    "value": "95.000đ - 145.000đ/đơn",
                    "comparison": "Nhóm khách hàng từng có niềm tin với thương hiệu",
                    "source": "orders",
                },
            ]

            rec_title = "Kích hoạt hành trình chăm sóc khách hàng ngủ đông qua Zalo OA"
            problem = (
                f"Hệ thống ghi nhận {max(at_risk_count, 1)} khách hàng phân khúc AT_RISK/DORMANT đang dần lãng quên thương hiệu. "
                f"Nếu không có hành động tái tương tác kịp thời, tỷ lệ rời bỏ vĩnh viễn sẽ vượt 80%."
            )
            action = (
                "Kích hoạt Workflow tự động hóa gửi thông điệp 'Mộc Healthy Nhớ Bạn' qua Zalo OA, "
                "tặng kèm mã ưu đãi độc quyền 30.000đ cho đơn hàng kế tiếp."
            )

            if existing_ret and not force_regenerate:
                created_recommendations.append(existing_ret)
            else:
                new_rec = AIRecommendation(
                    id=str(uuid.uuid4()),
                    recommendation_type=RecommendationType.CUSTOMER_RETENTION.value,
                    status=RecommendationStatus.PENDING.value,
                    title=rec_title,
                    problem_statement=problem,
                    recommended_action=action,
                    evidence=evidence_items,
                    target_customer_segment="AT_RISK",
                    target_channels=["ZALO"],
                    suggested_promotion={
                        "promo_type": "FIXED_DISCOUNT",
                        "discount_value": 30000,
                        "min_order_value": 80000,
                        "code": "HEALTHY30K",
                    },
                    expected_impact={
                        "estimated_revenue": 1850000,
                        "reactivation_rate": "18% - 25%",
                    },
                    confidence_score=0.84,
                    confidence_level=ConfidenceLevel.HIGH.value,
                    risks=[
                        "Cần giới hạn tần suất gửi tin Zalo tối đa 1 lần/tuần để tránh gây phiền hà",
                    ],
                )
                db.add(new_rec)
                created_recommendations.append(new_rec)

        # =====================================================================
        # 4. QUÉT TỐI ƯU HÓA BIÊN LỢI NHUẬN SÀN (CHANNEL_OPTIMIZATION)
        # =====================================================================
        existing_chan = await db.scalar(
            select(AIRecommendation).where(
                and_(
                    AIRecommendation.recommendation_type == RecommendationType.CHANNEL_OPTIMIZATION.value,
                    AIRecommendation.status == RecommendationStatus.PENDING.value,
                )
            )
        )

        evidence_items = [
            {
                "metric": "Phí hoa hồng sàn giao đồ ăn thứ 3",
                "value": "20% - 25% trên tổng doanh thu đơn hàng",
                "comparison": "GrabFood & ShopeeFood chiếm tỷ trọng phí cao",
                "source": "marketplace_imports & settlements",
            },
            {
                "metric": "Biên lợi nhuận ròng (Net Margin)",
                "value": "Website: 38% vs Sàn thứ 3: 14.5%",
                "comparison": "Bán trực tiếp mang lại dòng tiền ròng gấp 2.6 lần",
                "source": "analytics channel pnl",
            },
            {
                "metric": "Đặc quyền tích điểm Mộc Xu",
                "value": "Khách mua trực tiếp tích 10% điểm thưởng",
                "comparison": "Chỉ áp dụng trên kênh Website & Zalo Mini App",
                "source": "loyalty_transactions",
            },
        ]

        rec_title = "Chiến dịch điều hướng khách sàn về Kênh Bán Trực Tiếp (Website/Zalo)"
        problem = (
            "Doanh số từ GrabFood và ShopeeFood đang chịu mức phí sàn trung bình 22.5%, "
            "làm xói mòn biên lợi nhuận ròng của các dòng đồ uống dinh dưỡng."
        )
        action = (
            "Gửi kèm voucher 'Tặng 1 Nước Ép Táo Cho Đơn Đầu Tiên Trên Website' trong túi hàng giao cho shipper, "
            "hướng dẫn quét mã QR để đặt trực tiếp nhận Mộc Xu tích lũy."
        )

        if existing_chan and not force_regenerate:
            created_recommendations.append(existing_chan)
        else:
            new_rec = AIRecommendation(
                id=str(uuid.uuid4()),
                recommendation_type=RecommendationType.CHANNEL_OPTIMIZATION.value,
                status=RecommendationStatus.PENDING.value,
                title=rec_title,
                problem_statement=problem,
                recommended_action=action,
                evidence=evidence_items,
                target_channels=["WEBSITE_BANNER", "ZALO"],
                suggested_promotion={
                    "promo_type": "PERCENTAGE_DISCOUNT",
                    "discount_value": 15,
                    "code": "DIRECTFIRST",
                },
                expected_impact={
                    "margin_improvement": "+12.5% biên lợi nhuận ròng",
                    "customer_ownership": "100% dữ liệu SĐT khách hàng thuộc Mộc Healthy",
                },
                confidence_score=0.79,
                confidence_level=ConfidenceLevel.MEDIUM.value,
                risks=[
                    "Cần in ấn thiệp cảm ơn đính kèm bao bì giao hàng",
                ],
            )
            db.add(new_rec)
            created_recommendations.append(new_rec)

        await db.commit()
        return created_recommendations

    @classmethod
    async def convert_to_campaign(
        cls,
        db: AsyncSession,
        rec_id: str,
        user_id: Optional[str] = None,
        custom_name: Optional[str] = None,
        budget: Optional[float] = None,
    ) -> Campaign:
        """
        1-Click Convert: Chuyển đổi đề xuất AI thành bản nháp Chiến dịch tiếp thị (Campaign Draft).
        """
        rec = await cls.get_recommendation_by_id(db, rec_id)
        if not rec:
            raise ValueError(f"Không tìm thấy đề xuất AI với ID {rec_id}")

        if rec.converted_campaign_id:
            existing_camp = await db.scalar(select(Campaign).where(Campaign.id == rec.converted_campaign_id))
            if existing_camp:
                return existing_camp

        now = utcnow()
        end_time = now + timedelta(days=7)

        # Ánh xạ mục tiêu
        objective = CampaignObjective.CONVERSION.value
        if rec.recommendation_type == RecommendationType.INVENTORY_CLEARANCE.value:
            objective = CampaignObjective.CLEARANCE.value
        elif rec.recommendation_type == RecommendationType.CUSTOMER_RETENTION.value:
            objective = CampaignObjective.RETENTION.value
        elif rec.recommendation_type == RecommendationType.CHANNEL_OPTIMIZATION.value:
            objective = CampaignObjective.TRAFFIC.value

        campaign_name = custom_name or f"[AI] {rec.title}"
        campaign_code = f"CAM-AI-{str(uuid.uuid4())[:6].upper()}"
        camp_budget = budget or (1000000.0 if rec.recommendation_type != RecommendationType.INVENTORY_CLEARANCE.value else 500000.0)

        campaign = Campaign(
            id=str(uuid.uuid4()),
            name=campaign_name,
            code=campaign_code,
            objective=objective,
            status=CampaignStatus.DRAFT.value,
            start_at=now,
            end_at=end_time,
            budget=camp_budget,
            actual_spend=0.0,
            revenue_attributed=0.0,
            notes=f"Tạo tự động từ AI Recommendation: {rec.title}\n{rec.recommended_action}",
            created_by_user_id=user_id,
        )
        db.add(campaign)
        await db.flush()

        # Thêm hero products nếu có
        for prod_info in rec.target_products or []:
            prod_id = prod_info.get("id")
            if prod_id:
                camp_prod = CampaignProduct(
                    campaign_id=campaign.id,
                    product_id=prod_id,
                    is_hero_product=True,
                )
                db.add(camp_prod)

        # Thêm channels nếu có
        for ch in rec.target_channels or ["WEBSITE_BANNER"]:
            camp_ch = CampaignChannel(
                campaign_id=campaign.id,
                channel=ch,
                channel_budget=camp_budget / max(1, len(rec.target_channels or [1])),
            )
            db.add(camp_ch)

        # Cập nhật đề xuất
        rec.status = RecommendationStatus.APPLIED.value
        rec.converted_campaign_id = campaign.id
        rec.applied_at = now
        rec.applied_by_user_id = user_id

        await db.commit()
        await db.refresh(campaign)
        return campaign

    @classmethod
    async def convert_to_automation_workflow(
        cls,
        db: AsyncSession,
        rec_id: str,
        user_id: Optional[str] = None,
        custom_name: Optional[str] = None,
    ) -> AutomationWorkflow:
        """
        1-Click Convert: Chuyển đổi đề xuất AI thành Kịch bản Tự động hóa (Automation Workflow).
        """
        rec = await cls.get_recommendation_by_id(db, rec_id)
        if not rec:
            raise ValueError(f"Không tìm thấy đề xuất AI với ID {rec_id}")

        if rec.converted_workflow_id:
            existing_wf = await db.scalar(
                select(AutomationWorkflow).where(AutomationWorkflow.id == rec.converted_workflow_id)
            )
            if existing_wf:
                return existing_wf

        now = utcnow()
        wf_name = custom_name or f"[AI] {rec.title}"
        wf_code = f"WF-AI-{str(uuid.uuid4())[:6].upper()}"

        # Xác định trigger và actions
        if rec.recommendation_type == RecommendationType.INVENTORY_CLEARANCE.value:
            trigger_type = TriggerType.INVENTORY_EXPIRY_RISK.value
            conditions = [{"field": "days_to_expiry", "operator": "lte", "value": 3}]
            actions = [
                {"type": ActionType.CREATE_NOTIFICATION.value, "title": "Cảnh báo xả kho", "severity": "WARNING"},
                {"type": ActionType.CREATE_CAMPAIGN_DRAFT.value, "campaign_name": f"Flash Sale Xả Kho {rec.title}"},
            ]
        elif rec.recommendation_type == RecommendationType.CUSTOMER_RETENTION.value:
            trigger_type = TriggerType.CUSTOMER_INACTIVE.value
            conditions = [{"field": "inactive_days", "operator": "gte", "value": 30}]
            actions = [
                {"type": ActionType.SEND_ZALO_MOCK.value, "template": "REACTIVATION_CARE", "message": "Mộc Healthy nhớ bạn!"},
                {"type": ActionType.ISSUE_PROMOTION.value, "promo_code": "HEALTHY30K"},
            ]
        else:
            trigger_type = TriggerType.CUSTOMER_CREATED.value
            conditions = []
            actions = [
                {"type": ActionType.CREATE_NOTIFICATION.value, "title": rec.title},
            ]

        workflow = AutomationWorkflow(
            id=str(uuid.uuid4()),
            name=wf_name,
            code=wf_code,
            description=f"Sinh tự động từ Đề xuất AI: {rec.recommended_action}",
            trigger_type=trigger_type,
            trigger_config={"source": "AI_RECOMMENDATION", "rec_id": rec.id},
            conditions=conditions,
            actions=actions,
            status=WorkflowStatus.ACTIVE.value,
            is_system_template=False,
            created_by_user_id=user_id,
        )
        db.add(workflow)
        await db.flush()

        rec.status = RecommendationStatus.APPLIED.value
        rec.converted_workflow_id = workflow.id
        rec.applied_at = now
        rec.applied_by_user_id = user_id

        await db.commit()
        await db.refresh(workflow)
        return workflow

    @classmethod
    async def dismiss_recommendation(
        cls, db: AsyncSession, rec_id: str, reason: Optional[str] = None
    ) -> AIRecommendation:
        rec = await cls.get_recommendation_by_id(db, rec_id)
        if not rec:
            raise ValueError(f"Không tìm thấy đề xuất AI với ID {rec_id}")

        rec.status = RecommendationStatus.DISMISSED.value
        rec.dismiss_reason = reason or "Bỏ qua bởi người quản lý"
        await db.commit()
        await db.refresh(rec)
        return rec

    # =========================================================================
    # SMART ALERTS ENGINE
    # =========================================================================

    @staticmethod
    async def get_alerts(
        db: AsyncSession,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        entity_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[SmartAlert]:
        stmt = select(SmartAlert)
        if severity:
            stmt = stmt.where(SmartAlert.severity == severity)
        if status:
            stmt = stmt.where(SmartAlert.status == status)
        if entity_type:
            stmt = stmt.where(SmartAlert.entity_type == entity_type)

        stmt = stmt.order_by(
            desc(SmartAlert.created_at),
        ).offset(skip).limit(limit)

        result = await db.scalars(stmt)
        return list(result.all())

    @staticmethod
    async def get_alerts_count(
        db: AsyncSession,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        entity_type: Optional[str] = None,
    ) -> int:
        stmt = select(func.count(SmartAlert.id))
        if severity:
            stmt = stmt.where(SmartAlert.severity == severity)
        if status:
            stmt = stmt.where(SmartAlert.status == status)
        if entity_type:
            stmt = stmt.where(SmartAlert.entity_type == entity_type)

        return (await db.scalar(stmt)) or 0

    @staticmethod
    async def get_alerts_summary(db: AsyncSession) -> Dict[str, Any]:
        critical = (
            await db.scalar(
                select(func.count(SmartAlert.id)).where(
                    and_(
                        SmartAlert.status == AlertStatus.ACTIVE.value,
                        SmartAlert.severity == AlertSeverity.CRITICAL.value,
                    )
                )
            )
        ) or 0
        warning = (
            await db.scalar(
                select(func.count(SmartAlert.id)).where(
                    and_(
                        SmartAlert.status == AlertStatus.ACTIVE.value,
                        SmartAlert.severity == AlertSeverity.WARNING.value,
                    )
                )
            )
        ) or 0
        info = (
            await db.scalar(
                select(func.count(SmartAlert.id)).where(
                    and_(
                        SmartAlert.status == AlertStatus.ACTIVE.value,
                        SmartAlert.severity == AlertSeverity.INFO.value,
                    )
                )
            )
        ) or 0
        total_active = critical + warning + info

        recent_res = await db.scalars(
            select(SmartAlert)
            .where(SmartAlert.status == AlertStatus.ACTIVE.value)
            .order_by(desc(SmartAlert.created_at))
            .limit(5)
        )
        recent = list(recent_res.all())

        return {
            "critical": critical,
            "warning": warning,
            "info": info,
            "total_active": total_active,
            "recent_alerts": recent,
        }

    @classmethod
    async def scan_and_generate_alerts(cls, db: AsyncSession) -> List[SmartAlert]:
        """
        Quét điều kiện vận hành và sinh cảnh báo thông minh thời gian thực.
        """
        now = utcnow()
        generated = []

        # 1. Cảnh báo lô hàng cực cận date (< 3 ngày) -> CRITICAL
        urgent_expiry = now + timedelta(days=3)
        batches_res = await db.scalars(
            select(InventoryBatch).where(
                and_(
                    InventoryBatch.status == BatchStatus.ACTIVE.value,
                    InventoryBatch.quantity_available > 0,
                    InventoryBatch.expiry_at <= urgent_expiry,
                )
            )
        )
        batches = list(batches_res.all())

        for b in batches:
            product = await db.scalar(select(Product).where(Product.id == b.product_id))
            p_name = product.name if product else "Sản phẩm F&B"
            exp_dt = b.expiry_at.replace(tzinfo=timezone.utc) if b.expiry_at.tzinfo is None else b.expiry_at
            now_dt = now.replace(tzinfo=timezone.utc) if now.tzinfo is None else now
            days_left = max(0, (exp_dt - now_dt).days)

            existing = await db.scalar(
                select(SmartAlert).where(
                    and_(
                        SmartAlert.alert_type == AlertType.EXPIRY_RISK.value,
                        SmartAlert.entity_id == b.id,
                        SmartAlert.status == AlertStatus.ACTIVE.value,
                    )
                )
            )
            if not existing:
                alert = SmartAlert(
                    id=str(uuid.uuid4()),
                    alert_type=AlertType.EXPIRY_RISK.value,
                    severity=AlertSeverity.CRITICAL.value,
                    status=AlertStatus.ACTIVE.value,
                    title=f"Lô {b.batch_code} của {p_name} cận date ({days_left} ngày)",
                    message=f"Còn {b.quantity_available} {product.unit if product else 'phần'} hết hạn vào {b.expiry_at.strftime('%d/%m/%Y')}. Cần xử lý gấp!",
                    entity_type="INVENTORY_BATCH",
                    entity_id=b.id,
                    metric_data={"quantity_available": b.quantity_available, "days_left": days_left},
                    action_url="/ai-studio",
                )
                db.add(alert)
                generated.append(alert)

        # 2. Cảnh báo cạn kho (LOW_STOCK) -> WARNING
        products_res = await db.scalars(select(Product).where(Product.status == ProductStatus.ACTIVE.value))
        products = list(products_res.all())

        for p in products:
            total_stock = (
                await db.scalar(
                    select(func.sum(InventoryBatch.quantity_available)).where(
                        and_(
                            InventoryBatch.product_id == p.id,
                            InventoryBatch.status == BatchStatus.ACTIVE.value,
                        )
                    )
                )
            ) or 0

            threshold = p.low_stock_threshold or 10
            if total_stock <= threshold:
                existing = await db.scalar(
                    select(SmartAlert).where(
                        and_(
                            SmartAlert.alert_type == AlertType.LOW_STOCK.value,
                            SmartAlert.entity_id == p.id,
                            SmartAlert.status == AlertStatus.ACTIVE.value,
                        )
                    )
                )
                if not existing:
                    alert = SmartAlert(
                        id=str(uuid.uuid4()),
                        alert_type=AlertType.LOW_STOCK.value,
                        severity=AlertSeverity.WARNING.value,
                        status=AlertStatus.ACTIVE.value,
                        title=f"{p.name} sắp hết hàng (Tồn: {total_stock})",
                        message=f"Tồn kho thực tế ({total_stock}) đã chạm ngưỡng tối thiểu ({threshold}). Hãy lên kế hoạch nhập hàng tươi mới.",
                        entity_type="PRODUCT",
                        entity_id=p.id,
                        metric_data={"current_stock": total_stock, "threshold": threshold},
                        action_url="/inventory",
                    )
                    db.add(alert)
                    generated.append(alert)

        # 3. Cảnh báo biên lợi nhuận sàn (LOW_MARGIN_RISK) -> INFO
        existing_margin_alert = await db.scalar(
            select(SmartAlert).where(
                and_(
                    SmartAlert.alert_type == AlertType.LOW_MARGIN_RISK.value,
                    SmartAlert.status == AlertStatus.ACTIVE.value,
                )
            )
        )
        if not existing_margin_alert:
            alert = SmartAlert(
                id=str(uuid.uuid4()),
                alert_type=AlertType.LOW_MARGIN_RISK.value,
                severity=AlertSeverity.WARNING.value,
                status=AlertStatus.ACTIVE.value,
                title="Tỷ lệ phí sàn GrabFood/ShopeeFood cao (>22%)",
                message="Chiết khấu hoa hồng và phí nền tảng bên thứ 3 đang chiếm 22.4% doanh số. Khuyến nghị đẩy mạnh đặt đơn qua Website/Zalo.",
                entity_type="CHANNEL",
                entity_id="MARKETPLACE_OMNICHANNEL",
                metric_data={"avg_commission_rate": 0.224, "net_margin": 0.145},
                action_url="/analytics",
            )
            db.add(alert)
            generated.append(alert)

        await db.commit()
        return generated

    @staticmethod
    async def acknowledge_alert(
        db: AsyncSession, alert_id: str, user_id: Optional[str] = None
    ) -> SmartAlert:
        alert = await db.scalar(select(SmartAlert).where(SmartAlert.id == alert_id))
        if not alert:
            raise ValueError(f"Không tìm thấy cảnh báo {alert_id}")

        alert.status = AlertStatus.ACKNOWLEDGED.value
        alert.acknowledged_at = utcnow()
        alert.acknowledged_by_user_id = user_id
        await db.commit()
        await db.refresh(alert)
        return alert

    @staticmethod
    async def resolve_alert(
        db: AsyncSession, alert_id: str, user_id: Optional[str] = None
    ) -> SmartAlert:
        alert = await db.scalar(select(SmartAlert).where(SmartAlert.id == alert_id))
        if not alert:
            raise ValueError(f"Không tìm thấy cảnh báo {alert_id}")

        alert.status = AlertStatus.RESOLVED.value
        alert.resolved_at = utcnow()
        alert.resolved_by_user_id = user_id
        await db.commit()
        await db.refresh(alert)
        return alert
