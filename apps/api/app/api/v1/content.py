import math
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, require_permission
from app.models.auth import User
from app.schemas.content import (
    ContentCreateInput,
    ContentUpdateInput,
    AIGenerateRequest,
    AIGenerateResponse,
    ContentScheduleRequest,
    ContentStatusUpdateRequest,
    ContentListItem,
    ContentListResponse,
    ContentDetailResponse,
    ContentCalendarItem,
    ContentOverviewStats,
)
from app.services.content_service import ContentService
from app.services.ai_content_service import AIContentService

router = APIRouter(prefix="/content", tags=["Content Studio & Social Publisher"])


@router.get("/overview", response_model=ContentOverviewStats)
async def get_content_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lấy thống kê tổng quan nội dung tiếp thị:
    Tổng bài, đã xuất bản, đã lên lịch, đang chờ duyệt, bản nháp, bài sinh bởi AI.
    """
    return await ContentService.get_overview_stats(db)


@router.get("/calendar", response_model=List[ContentCalendarItem])
async def list_calendar_content(
    start_date: Optional[datetime] = Query(None, description="Bắt đầu từ ngày"),
    end_date: Optional[datetime] = Query(None, description="Đến ngày"),
    channel: Optional[str] = Query(None, description="Lọc theo kênh"),
    status: Optional[str] = Query(None, description="Lọc theo trạng thái"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lấy danh sách các bài viết theo lịch phát hành (Content Calendar).
    Mặc định lấy trong vòng 30 ngày (từ 7 ngày trước đến 23 ngày sau).
    """
    now = datetime.now(timezone.utc)
    s_date = start_date or (now - timedelta(days=7))
    e_date = end_date or (now + timedelta(days=23))

    return await ContentService.list_calendar(
        db=db,
        start_date=s_date,
        end_date=e_date,
        channel=channel,
        status=status,
    )


@router.get("", response_model=ContentListResponse)
async def list_content(
    channel: Optional[str] = Query(None, description="Lọc theo kênh phân phối"),
    status: Optional[str] = Query(None, description="Lọc theo trạng thái bài viết"),
    campaign_id: Optional[str] = Query(None, description="Lọc theo chiến dịch"),
    product_id: Optional[str] = Query(None, description="Lọc theo sản phẩm"),
    search: Optional[str] = Query(None, description="Tìm kiếm theo tiêu đề hoặc nội dung"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lấy danh sách nội dung tiếp thị với phân trang, bộ lọc và tìm kiếm.
    """
    items, total = await ContentService.list_content(
        db=db,
        channel=channel,
        status=status,
        campaign_id=campaign_id,
        product_id=product_id,
        search=search,
        page=page,
        page_size=page_size,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    list_items = []
    for it in items:
        body_snip = it.body[:140] + "..." if len(it.body) > 140 else it.body
        list_items.append(
            ContentListItem(
                id=it.id,
                title=it.title,
                content_type=it.content_type,
                channel=it.channel,
                status=it.status,
                brand_tone=it.brand_tone,
                hook=it.hook,
                body_snippet=body_snip,
                cta=it.cta,
                hashtags=it.hashtags or [],
                media_asset_ids=it.media_asset_ids or [],
                campaign_id=it.campaign_id,
                campaign_name=it.campaign.name if it.campaign else None,
                product_id=it.product_id,
                product_name=it.product.name if it.product else None,
                ai_generated=it.ai_generated,
                ai_model=it.ai_model,
                scheduled_at=it.scheduled_at,
                published_at=it.published_at,
                external_post_url=it.external_post_url,
                created_at=it.created_at,
            )
        )

    return ContentListResponse(
        items=list_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("/generate-ai", response_model=AIGenerateResponse)
async def generate_ai_content(
    payload: AIGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("content.create")),
):
    """
    Sáng tạo nội dung tự động bằng AI Content Studio:
    Tự động kết hợp thông tin sản phẩm, mục tiêu chiến dịch, định dạng kênh và giọng điệu thương hiệu.
    """
    return await AIContentService.generate_content(db=db, req=payload)


@router.post("", response_model=ContentDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_content(
    payload: ContentCreateInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("content.create")),
):
    """
    Tạo bài viết/nội dung mới ở trạng thái Bản nháp (DRAFT).
    """
    item = await ContentService.create_content(
        db=db,
        data=payload,
        user_id=current_user.id,
    )
    return ContentService.format_detail_response(item)


@router.get("/{content_id}", response_model=ContentDetailResponse)
async def get_content_detail(
    content_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Xem chi tiết bài viết, kịch bản, hashtag, thông tin mạng xã hội.
    """
    item = await ContentService.get_by_id(db, content_id)
    return ContentService.format_detail_response(item)


@router.put("/{content_id}", response_model=ContentDetailResponse)
async def update_content(
    content_id: str,
    payload: ContentUpdateInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("content.create")),
):
    """
    Chỉnh sửa nội dung bài viết tiếp thị.
    """
    item = await ContentService.update_content(
        db=db,
        content_id=content_id,
        data=payload,
    )
    return ContentService.format_detail_response(item)


@router.post("/{content_id}/submit-review", response_model=ContentDetailResponse)
async def submit_for_review(
    content_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("content.create")),
):
    """
    Gửi duyệt bài viết tiếp thị (DRAFT / AI_GENERATED -> IN_REVIEW).
    """
    item = await ContentService.submit_for_review(db=db, content_id=content_id)
    return ContentService.format_detail_response(item)


@router.post("/{content_id}/approve", response_model=ContentDetailResponse)
async def approve_content(
    content_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("content.approve")),
):
    """
    Phê duyệt bài viết trước khi xuất bản (IN_REVIEW -> APPROVED).
    Yêu cầu quyền content.approve.
    """
    item = await ContentService.approve_content(
        db=db,
        content_id=content_id,
        user_id=current_user.id,
    )
    return ContentService.format_detail_response(item)


@router.post("/{content_id}/schedule", response_model=ContentDetailResponse)
async def schedule_content(
    content_id: str,
    payload: ContentScheduleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("content.publish")),
):
    """
    Lên lịch phát hành bài viết lên mạng xã hội (APPROVED -> SCHEDULED).
    Yêu cầu quyền content.publish.
    """
    item = await ContentService.schedule_content(
        db=db,
        content_id=content_id,
        scheduled_at=payload.scheduled_at,
    )
    return ContentService.format_detail_response(item)


@router.post("/{content_id}/publish", response_model=ContentDetailResponse)
async def publish_content_now(
    content_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("content.publish")),
):
    """
    Xuất bản bài viết ngay lập tức lên mạng xã hội (Facebook, Zalo OA, TikTok, Instagram).
    Yêu cầu quyền content.publish.
    """
    item = await ContentService.publish_now(db=db, content_id=content_id)
    return ContentService.format_detail_response(item)


@router.post("/{content_id}/status", response_model=ContentDetailResponse)
async def update_content_status(
    content_id: str,
    payload: ContentStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("content.create")),
):
    """
    Cập nhật trạng thái bài viết: ARCHIVED, FAILED, DRAFT...
    """
    item = await ContentService.update_status(
        db=db,
        content_id=content_id,
        new_status=payload.status,
        reason=payload.reason,
    )
    return ContentService.format_detail_response(item)


@router.delete("/{content_id}")
async def delete_content(
    content_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("content.create")),
):
    """
    Xóa bài viết (chỉ cho phép khi chưa xuất bản lên mạng xã hội).
    """
    await ContentService.delete_content(db=db, content_id=content_id)
    return {"message": "Đã xóa bài viết thành công"}
