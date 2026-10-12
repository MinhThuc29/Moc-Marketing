from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, func, or_, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.campaign import (
    Campaign,
    CampaignChannel,
    CampaignProduct,
    CampaignStatus,
    CampaignObjective,
)
from app.models.product import Product
from app.models.promotion import Promotion
from app.models.auth import User
from app.schemas.campaign import (
    CampaignCreateInput,
    CampaignUpdateInput,
    CampaignDetailResponse,
    CampaignChannelResponse,
    CampaignProductResponse,
    CampaignOverviewStats,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CampaignService:
    @staticmethod
    async def get_by_id(db: AsyncSession, campaign_id: str) -> Campaign:
        stmt = (
            select(Campaign)
            .where(Campaign.id == campaign_id)
            .options(
                selectinload(Campaign.channels),
                selectinload(Campaign.products).selectinload(CampaignProduct.product),
                selectinload(Campaign.promotion),
                selectinload(Campaign.created_by_user),
                selectinload(Campaign.approved_by_user),
            )
        )
        res = await db.execute(stmt)
        camp = res.scalar_one_or_none()
        if not camp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy chiến dịch marketing với mã {campaign_id}",
            )
        return camp

    @staticmethod
    async def get_by_code(db: AsyncSession, code: str) -> Optional[Campaign]:
        res = await db.execute(
            select(Campaign).where(Campaign.code == code.strip().upper())
        )
        return res.scalar_one_or_none()

    @staticmethod
    async def create_campaign(
        db: AsyncSession,
        data: CampaignCreateInput,
        user_id: Optional[str] = None,
    ) -> Campaign:
        clean_code = data.code.strip().upper()
        existing = await CampaignService.get_by_code(db, clean_code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Mã chiến dịch '{clean_code}' đã tồn tại trong hệ thống.",
            )

        if data.end_at <= data.start_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Thời gian kết thúc chiến dịch phải sau thời gian bắt đầu.",
            )

        camp = Campaign(
            name=data.name.strip(),
            code=clean_code,
            objective=data.objective or CampaignObjective.CONVERSION.value,
            status=CampaignStatus.DRAFT.value,
            start_at=data.start_at,
            end_at=data.end_at,
            budget=float(data.budget or 0.0),
            actual_spend=0.0,
            revenue_attributed=0.0,
            target_audience=data.target_audience or [],
            promotion_id=data.promotion_id,
            landing_page=data.landing_page,
            utm_source=data.utm_source,
            utm_medium=data.utm_medium,
            utm_campaign=data.utm_campaign or clean_code.lower(),
            notes=data.notes,
            created_by_user_id=user_id,
        )
        db.add(camp)
        await db.flush()

        # Add channels
        if data.channels:
            for ch in data.channels:
                c_channel = CampaignChannel(
                    campaign_id=camp.id,
                    channel=ch.channel.upper(),
                    channel_budget=float(ch.channel_budget or 0.0),
                    target_metric=ch.target_metric,
                    notes=ch.notes,
                )
                db.add(c_channel)

        # Add products
        if data.products:
            for pr in data.products:
                c_prod = CampaignProduct(
                    campaign_id=camp.id,
                    product_id=pr.product_id,
                    is_hero_product=pr.is_hero_product,
                    special_price=pr.special_price,
                )
                db.add(c_prod)

        await db.flush()
        await db.commit()
        return await CampaignService.get_by_id(db, camp.id)

    @staticmethod
    async def update_campaign(
        db: AsyncSession,
        campaign_id: str,
        data: CampaignUpdateInput,
    ) -> Campaign:
        camp = await CampaignService.get_by_id(db, campaign_id)

        if data.start_at or data.end_at:
            new_start = data.start_at or camp.start_at
            new_end = data.end_at or camp.end_at
            if new_end <= new_start:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Thời gian kết thúc chiến dịch phải sau thời gian bắt đầu.",
                )
            camp.start_at = new_start
            camp.end_at = new_end

        if data.name is not None:
            camp.name = data.name.strip()
        if data.objective is not None:
            camp.objective = data.objective
        if data.budget is not None:
            camp.budget = float(data.budget)
        if data.target_audience is not None:
            camp.target_audience = data.target_audience
        if data.promotion_id is not None:
            camp.promotion_id = data.promotion_id
        if data.landing_page is not None:
            camp.landing_page = data.landing_page
        if data.notes is not None:
            camp.notes = data.notes

        # Replace channels if provided
        if data.channels is not None:
            for old_ch in camp.channels:
                await db.delete(old_ch)
            for ch in data.channels:
                c_channel = CampaignChannel(
                    campaign_id=camp.id,
                    channel=ch.channel.upper(),
                    channel_budget=float(ch.channel_budget or 0.0),
                    target_metric=ch.target_metric,
                    notes=ch.notes,
                )
                db.add(c_channel)

        # Replace products if provided
        if data.products is not None:
            for old_pr in camp.products:
                await db.delete(old_pr)
            for pr in data.products:
                c_prod = CampaignProduct(
                    campaign_id=camp.id,
                    product_id=pr.product_id,
                    is_hero_product=pr.is_hero_product,
                    special_price=pr.special_price,
                )
                db.add(c_prod)

        await db.flush()
        await db.commit()
        return await CampaignService.get_by_id(db, camp.id)

    @staticmethod
    async def submit_for_review(db: AsyncSession, campaign_id: str) -> Campaign:
        camp = await CampaignService.get_by_id(db, campaign_id)
        if camp.status not in (CampaignStatus.DRAFT.value, CampaignStatus.PLANNING.value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Chỉ có thể gửi duyệt chiến dịch ở trạng thái Bản nháp (DRAFT). Trạng thái hiện tại: {camp.status}",
            )
        camp.status = CampaignStatus.READY_FOR_REVIEW.value
        await db.flush()
        await db.commit()
        return await CampaignService.get_by_id(db, camp.id)

    @staticmethod
    async def approve_campaign(
        db: AsyncSession,
        campaign_id: str,
        user_id: str,
    ) -> Campaign:
        camp = await CampaignService.get_by_id(db, campaign_id)
        camp.status = CampaignStatus.APPROVED.value
        camp.approved_by_user_id = user_id
        camp.approved_at = utc_now()
        await db.flush()
        await db.commit()
        return await CampaignService.get_by_id(db, camp.id)

    @staticmethod
    async def update_status(
        db: AsyncSession,
        campaign_id: str,
        new_status: str,
    ) -> Campaign:
        valid_statuses = [s.value for s in CampaignStatus]
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Trạng thái '{new_status}' không hợp lệ. Phải là một trong: {', '.join(valid_statuses)}",
            )
        camp = await CampaignService.get_by_id(db, campaign_id)
        camp.status = new_status
        await db.flush()
        await db.commit()
        return await CampaignService.get_by_id(db, camp.id)

    @staticmethod
    async def delete_campaign(db: AsyncSession, campaign_id: str) -> bool:
        camp = await CampaignService.get_by_id(db, campaign_id)
        if camp.status in (CampaignStatus.ACTIVE.value, CampaignStatus.COMPLETED.value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không thể xóa chiến dịch đang hoạt động hoặc đã hoàn thành. Hãy chuyển sang Tạm dừng (PAUSED) hoặc Đã hủy (CANCELLED).",
            )
        await db.delete(camp)
        await db.flush()
        await db.commit()
        return True

    @staticmethod
    async def list_campaigns(
        db: AsyncSession,
        status: Optional[str] = None,
        objective: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Campaign], int]:
        stmt = (
            select(Campaign)
            .options(
                selectinload(Campaign.channels),
                selectinload(Campaign.products),
            )
        )

        if status:
            stmt = stmt.where(Campaign.status == status)
        if objective:
            stmt = stmt.where(Campaign.objective == objective)
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Campaign.name.ilike(term),
                    Campaign.code.ilike(term),
                    Campaign.notes.ilike(term),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_res = await db.execute(count_stmt)
        total = total_res.scalar_one()

        stmt = stmt.order_by(desc(Campaign.start_at))
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        res = await db.execute(stmt)
        items = list(res.scalars().all())
        return items, total

    @staticmethod
    def format_detail_response(camp: Campaign) -> CampaignDetailResponse:
        actual_spend = float(camp.actual_spend or 0.0)
        revenue_attr = float(camp.revenue_attributed or 0.0)
        roi = 0.0
        if actual_spend > 0:
            roi = round(((revenue_attr - actual_spend) / actual_spend) * 100, 1)

        channel_responses = [
            CampaignChannelResponse(
                id=c.id,
                campaign_id=c.campaign_id,
                channel=c.channel,
                channel_budget=float(c.channel_budget or 0.0),
                channel_spend=float(c.channel_spend or 0.0),
                status=c.status,
                target_metric=c.target_metric,
                notes=c.notes,
                created_at=c.created_at,
            )
            for c in camp.channels
        ]

        product_responses = [
            CampaignProductResponse(
                id=p.id,
                campaign_id=p.campaign_id,
                product_id=p.product_id,
                product_name=p.product.name if p.product else "Sản phẩm",
                product_price=float(p.product.sale_price or p.product.base_price) if p.product else 0.0,
                is_hero_product=p.is_hero_product,
                special_price=float(p.special_price) if p.special_price else None,
                created_at=p.created_at,
            )
            for p in camp.products
        ]

        return CampaignDetailResponse(
            id=camp.id,
            name=camp.name,
            code=camp.code,
            objective=camp.objective,
            status=camp.status,
            start_at=camp.start_at,
            end_at=camp.end_at,
            budget=float(camp.budget or 0.0),
            actual_spend=actual_spend,
            revenue_attributed=revenue_attr,
            roi_percentage=roi,
            target_audience=camp.target_audience or [],
            promotion_id=camp.promotion_id,
            promotion_name=camp.promotion.name if camp.promotion else None,
            landing_page=camp.landing_page,
            utm_source=camp.utm_source,
            utm_medium=camp.utm_medium,
            utm_campaign=camp.utm_campaign,
            notes=camp.notes,
            created_by_user_id=camp.created_by_user_id,
            created_by_user_name=camp.created_by_user.full_name if camp.created_by_user else None,
            approved_by_user_id=camp.approved_by_user_id,
            approved_by_user_name=camp.approved_by_user.full_name if camp.approved_by_user else None,
            approved_at=camp.approved_at,
            channels=channel_responses,
            products=product_responses,
            created_at=camp.created_at,
            updated_at=camp.updated_at,
        )

    @staticmethod
    async def get_overview_stats(db: AsyncSession) -> CampaignOverviewStats:
        # Active campaigns
        res_active = await db.execute(
            select(func.count(Campaign.id)).where(Campaign.status == CampaignStatus.ACTIVE.value)
        )
        active_cnt = res_active.scalar_one() or 0

        # Ready for review
        res_review = await db.execute(
            select(func.count(Campaign.id)).where(Campaign.status == CampaignStatus.READY_FOR_REVIEW.value)
        )
        review_cnt = res_review.scalar_one() or 0

        # Total budget approved
        res_budget = await db.execute(
            select(func.sum(Campaign.budget)).where(
                Campaign.status.in_([
                    CampaignStatus.APPROVED.value,
                    CampaignStatus.ACTIVE.value,
                    CampaignStatus.COMPLETED.value,
                ])
            )
        )
        tot_budget = float(res_budget.scalar_one() or 0.0)

        # Total revenue attributed
        res_rev = await db.execute(select(func.sum(Campaign.revenue_attributed)))
        tot_rev = float(res_rev.scalar_one() or 0.0)

        # Total spend for ROI
        res_spend = await db.execute(select(func.sum(Campaign.actual_spend)))
        tot_spend = float(res_spend.scalar_one() or 0.0)

        avg_roi = 0.0
        if tot_spend > 0:
            avg_roi = round(((tot_rev - tot_spend) / tot_spend) * 100, 1)

        return CampaignOverviewStats(
            active_campaigns=active_cnt,
            ready_for_review_campaigns=review_cnt,
            total_budget_approved=tot_budget,
            total_revenue_attributed=tot_rev,
            average_roi_percentage=avg_roi,
        )
