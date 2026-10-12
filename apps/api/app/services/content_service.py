from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, func, or_, desc, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.content import (
    ContentItem,
    ContentType,
    ContentChannel,
    ContentStatus,
    BrandTone,
)
from app.models.campaign import Campaign
from app.models.product import Product
from app.models.auth import User
from app.schemas.content import (
    ContentCreateInput,
    ContentUpdateInput,
    ContentListItem,
    ContentDetailResponse,
    ContentCalendarItem,
    ContentOverviewStats,
)
from app.services.social_publisher_service import SocialPublisherService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ContentService:
    @staticmethod
    async def get_by_id(db: AsyncSession, content_id: str) -> ContentItem:
        stmt = (
            select(ContentItem)
            .where(ContentItem.id == content_id)
            .options(
                selectinload(ContentItem.campaign),
                selectinload(ContentItem.product),
                selectinload(ContentItem.created_by_user),
                selectinload(ContentItem.approved_by_user),
            )
        )
        res = await db.execute(stmt)
        item = res.scalar_one_or_none()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy bài viết/nội dung tiếp thị với mã {content_id}",
            )
        return item

    @staticmethod
    async def create_content(
        db: AsyncSession,
        data: ContentCreateInput,
        user_id: Optional[str] = None,
        ai_generated: bool = False,
        ai_model: Optional[str] = None,
        ai_prompt: Optional[str] = None,
    ) -> ContentItem:
        init_status = ContentStatus.AI_GENERATED.value if ai_generated else ContentStatus.DRAFT.value
        if data.scheduled_at:
            init_status = ContentStatus.SCHEDULED.value

        item = ContentItem(
            title=data.title.strip(),
            content_type=data.content_type.upper(),
            channel=data.channel.upper(),
            status=init_status,
            brand_tone=data.brand_tone.upper(),
            hook=data.hook.strip() if data.hook else None,
            body=data.body.strip(),
            cta=data.cta.strip() if data.cta else None,
            hashtags=data.hashtags or [],
            media_asset_ids=data.media_asset_ids or [],
            campaign_id=data.campaign_id,
            product_id=data.product_id,
            ai_generated=ai_generated,
            ai_model=ai_model,
            ai_prompt=ai_prompt,
            scheduled_at=data.scheduled_at,
            created_by_user_id=user_id,
            metrics={},
        )
        db.add(item)
        await db.flush()
        await db.commit()
        return await ContentService.get_by_id(db, item.id)

    @staticmethod
    async def update_content(
        db: AsyncSession,
        content_id: str,
        data: ContentUpdateInput,
    ) -> ContentItem:
        item = await ContentService.get_by_id(db, content_id)

        if data.title is not None:
            item.title = data.title.strip()
        if data.content_type is not None:
            item.content_type = data.content_type.upper()
        if data.channel is not None:
            item.channel = data.channel.upper()
        if data.brand_tone is not None:
            item.brand_tone = data.brand_tone.upper()
        if data.hook is not None:
            item.hook = data.hook.strip() if data.hook else None
        if data.body is not None:
            item.body = data.body.strip()
        if data.cta is not None:
            item.cta = data.cta.strip() if data.cta else None
        if data.hashtags is not None:
            item.hashtags = data.hashtags
        if data.media_asset_ids is not None:
            item.media_asset_ids = data.media_asset_ids
        if data.campaign_id is not None:
            item.campaign_id = data.campaign_id
        if data.product_id is not None:
            item.product_id = data.product_id
        if data.scheduled_at is not None:
            item.scheduled_at = data.scheduled_at

        await db.flush()
        await db.commit()
        return await ContentService.get_by_id(db, item.id)

    @staticmethod
    async def submit_for_review(db: AsyncSession, content_id: str) -> ContentItem:
        item = await ContentService.get_by_id(db, content_id)
        if item.status not in (ContentStatus.DRAFT.value, ContentStatus.AI_GENERATED.value, ContentStatus.FAILED.value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Chỉ có thể gửi duyệt nội dung ở trạng thái DRAFT hoặc AI_GENERATED. Trạng thái hiện tại: {item.status}",
            )
        item.status = ContentStatus.IN_REVIEW.value
        await db.flush()
        await db.commit()
        return await ContentService.get_by_id(db, item.id)

    @staticmethod
    async def approve_content(
        db: AsyncSession,
        content_id: str,
        user_id: str,
    ) -> ContentItem:
        item = await ContentService.get_by_id(db, content_id)
        item.status = ContentStatus.APPROVED.value
        item.approved_by_user_id = user_id
        item.approved_at = utc_now()
        await db.flush()
        await db.commit()
        return await ContentService.get_by_id(db, item.id)

    @staticmethod
    async def schedule_content(
        db: AsyncSession,
        content_id: str,
        scheduled_at: datetime,
    ) -> ContentItem:
        item = await ContentService.get_by_id(db, content_id)
        if item.status not in (ContentStatus.APPROVED.value, ContentStatus.DRAFT.value, ContentStatus.AI_GENERATED.value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Nội dung cần được phê duyệt hoặc ở trạng thái nháp trước khi lên lịch đăng. Trạng thái hiện tại: {item.status}",
            )
        item.status = ContentStatus.SCHEDULED.value
        item.scheduled_at = scheduled_at
        await db.flush()
        await db.commit()
        return await ContentService.get_by_id(db, item.id)

    @staticmethod
    async def publish_now(db: AsyncSession, content_id: str) -> ContentItem:
        item = await ContentService.get_by_id(db, content_id)
        # Mark publishing state
        item.status = ContentStatus.PUBLISHING.value
        await db.flush()

        # Call social media publisher
        success, ext_id, ext_url, initial_metrics = SocialPublisherService.publish(item)

        if success:
            item.status = ContentStatus.PUBLISHED.value
            item.published_at = utc_now()
            item.external_post_id = ext_id
            item.external_post_url = ext_url
            item.metrics = initial_metrics
            item.error_message = None
        else:
            item.status = ContentStatus.FAILED.value
            item.error_message = "Không thể kết nối đến máy chủ mạng xã hội"
            item.retry_count += 1

        await db.flush()
        await db.commit()
        return await ContentService.get_by_id(db, item.id)

    @staticmethod
    async def update_status(
        db: AsyncSession,
        content_id: str,
        new_status: str,
        reason: Optional[str] = None,
    ) -> ContentItem:
        valid_statuses = [s.value for s in ContentStatus]
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Trạng thái '{new_status}' không hợp lệ. Phải là một trong: {', '.join(valid_statuses)}",
            )
        item = await ContentService.get_by_id(db, content_id)
        item.status = new_status
        if reason:
            item.error_message = reason
        await db.flush()
        await db.commit()
        return await ContentService.get_by_id(db, item.id)

    @staticmethod
    async def delete_content(db: AsyncSession, content_id: str) -> bool:
        item = await ContentService.get_by_id(db, content_id)
        if item.status == ContentStatus.PUBLISHED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể xóa bài viết đã xuất bản lên mạng xã hội. Hãy chuyển sang Lưu trữ (ARCHIVED).",
            )
        await db.delete(item)
        await db.flush()
        await db.commit()
        return True

    @staticmethod
    async def list_content(
        db: AsyncSession,
        channel: Optional[str] = None,
        status: Optional[str] = None,
        campaign_id: Optional[str] = None,
        product_id: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[ContentItem], int]:
        stmt = (
            select(ContentItem)
            .options(
                selectinload(ContentItem.campaign),
                selectinload(ContentItem.product),
            )
        )

        if channel:
            stmt = stmt.where(ContentItem.channel == channel.upper())
        if status:
            stmt = stmt.where(ContentItem.status == status.upper())
        if campaign_id:
            stmt = stmt.where(ContentItem.campaign_id == campaign_id)
        if product_id:
            stmt = stmt.where(ContentItem.product_id == product_id)
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    ContentItem.title.ilike(term),
                    ContentItem.body.ilike(term),
                    ContentItem.hook.ilike(term),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_res = await db.execute(count_stmt)
        total = total_res.scalar_one()

        stmt = stmt.order_by(desc(ContentItem.created_at))
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        res = await db.execute(stmt)
        items = list(res.scalars().all())
        return items, total

    @staticmethod
    async def list_calendar(
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        channel: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[ContentCalendarItem]:
        stmt = (
            select(ContentItem)
            .options(
                selectinload(ContentItem.campaign),
                selectinload(ContentItem.product),
            )
            .where(
                or_(
                    and_(ContentItem.scheduled_at >= start_date, ContentItem.scheduled_at <= end_date),
                    and_(ContentItem.published_at >= start_date, ContentItem.published_at <= end_date),
                )
            )
        )
        if channel:
            stmt = stmt.where(ContentItem.channel == channel.upper())
        if status:
            stmt = stmt.where(ContentItem.status == status.upper())

        stmt = stmt.order_by(ContentItem.scheduled_at.asc())
        res = await db.execute(stmt)
        items = list(res.scalars().all())

        calendar_items = []
        for it in items:
            calendar_items.append(
                ContentCalendarItem(
                    id=it.id,
                    title=it.title,
                    content_type=it.content_type,
                    channel=it.channel,
                    status=it.status,
                    scheduled_at=it.scheduled_at,
                    published_at=it.published_at,
                    campaign_name=it.campaign.name if it.campaign else None,
                    product_name=it.product.name if it.product else None,
                )
            )
        return calendar_items

    @staticmethod
    def format_detail_response(item: ContentItem) -> ContentDetailResponse:
        prod_price = None
        if item.product:
            prod_price = float(item.product.sale_price or item.product.base_price)

        return ContentDetailResponse(
            id=item.id,
            title=item.title,
            content_type=item.content_type,
            channel=item.channel,
            status=item.status,
            brand_tone=item.brand_tone,
            hook=item.hook,
            body=item.body,
            cta=item.cta,
            hashtags=item.hashtags or [],
            media_asset_ids=item.media_asset_ids or [],
            campaign_id=item.campaign_id,
            campaign_name=item.campaign.name if item.campaign else None,
            product_id=item.product_id,
            product_name=item.product.name if item.product else None,
            product_price=prod_price,
            ai_generated=item.ai_generated,
            ai_model=item.ai_model,
            ai_prompt=item.ai_prompt,
            scheduled_at=item.scheduled_at,
            published_at=item.published_at,
            external_post_id=item.external_post_id,
            external_post_url=item.external_post_url,
            error_message=item.error_message,
            retry_count=item.retry_count,
            metrics=item.metrics or {},
            created_by_user_id=item.created_by_user_id,
            created_by_user_name=item.created_by_user.full_name if item.created_by_user else None,
            approved_by_user_id=item.approved_by_user_id,
            approved_by_user_name=item.approved_by_user.full_name if item.approved_by_user else None,
            approved_at=item.approved_at,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    async def get_overview_stats(db: AsyncSession) -> ContentOverviewStats:
        res_tot = await db.execute(select(func.count(ContentItem.id)))
        tot = res_tot.scalar_one() or 0

        res_pub = await db.execute(
            select(func.count(ContentItem.id)).where(ContentItem.status == ContentStatus.PUBLISHED.value)
        )
        pub = res_pub.scalar_one() or 0

        res_sch = await db.execute(
            select(func.count(ContentItem.id)).where(ContentItem.status == ContentStatus.SCHEDULED.value)
        )
        sch = res_sch.scalar_one() or 0

        res_rev = await db.execute(
            select(func.count(ContentItem.id)).where(ContentItem.status == ContentStatus.IN_REVIEW.value)
        )
        rev = res_rev.scalar_one() or 0

        res_drf = await db.execute(
            select(func.count(ContentItem.id)).where(
                ContentItem.status.in_([ContentStatus.DRAFT.value, ContentStatus.AI_GENERATED.value])
            )
        )
        drf = res_drf.scalar_one() or 0

        res_ai = await db.execute(
            select(func.count(ContentItem.id)).where(ContentItem.ai_generated == True)
        )
        ai_cnt = res_ai.scalar_one() or 0

        return ContentOverviewStats(
            total_items=tot,
            published_items=pub,
            scheduled_items=sch,
            in_review_items=rev,
            draft_items=drf,
            ai_generated_items=ai_cnt,
        )
