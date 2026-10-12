import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, require_permission
from app.models.auth import User
from app.schemas.campaign import (
    CampaignCreateInput,
    CampaignUpdateInput,
    CampaignStatusUpdateRequest,
    CampaignListItem,
    CampaignListResponse,
    CampaignDetailResponse,
    CampaignOverviewStats,
)
from app.services.campaign_service import CampaignService

router = APIRouter(prefix="/campaigns", tags=["Campaign & Marketing Hub"])


@router.get("/overview", response_model=CampaignOverviewStats)
async def get_campaign_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lấy số liệu thống kê tổng quan các chiến dịch tiếp thị:
    Chiến dịch đang chạy, chờ duyệt, tổng ngân sách đã duyệt, doanh thu ghi nhận, tỷ lệ ROI.
    """
    return await CampaignService.get_overview_stats(db)


@router.get("", response_model=CampaignListResponse)
async def list_campaigns(
    status: Optional[str] = Query(None, description="Lọc theo trạng thái chiến dịch"),
    objective: Optional[str] = Query(None, description="Lọc theo mục tiêu chiến dịch"),
    search: Optional[str] = Query(None, description="Tìm theo tên, mã hoặc ghi chú"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lấy danh sách các chiến dịch tiếp thị với phân trang, bộ lọc và tìm kiếm.
    """
    items, total = await CampaignService.list_campaigns(
        db=db,
        status=status,
        objective=objective,
        search=search,
        page=page,
        page_size=page_size,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    list_items = []
    for c in items:
        actual_spend = float(c.actual_spend or 0.0)
        revenue_attr = float(c.revenue_attributed or 0.0)
        roi = 0.0
        if actual_spend > 0:
            roi = round(((revenue_attr - actual_spend) / actual_spend) * 100, 1)

        list_items.append(
            CampaignListItem(
                id=c.id,
                name=c.name,
                code=c.code,
                objective=c.objective,
                status=c.status,
                start_at=c.start_at,
                end_at=c.end_at,
                budget=float(c.budget or 0.0),
                actual_spend=actual_spend,
                revenue_attributed=revenue_attr,
                roi_percentage=roi,
                target_audience=c.target_audience or [],
                channels_count=len(c.channels),
                products_count=len(c.products),
                created_at=c.created_at,
            )
        )

    return CampaignListResponse(
        items=list_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=CampaignDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CampaignCreateInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("campaign.create")),
):
    """
    Tạo chiến dịch tiếp thị mới ở trạng thái Bản nháp (DRAFT).
    Yêu cầu quyền campaign.create.
    """
    camp = await CampaignService.create_campaign(
        db=db,
        data=payload,
        user_id=current_user.id,
    )
    return CampaignService.format_detail_response(camp)


@router.get("/{campaign_id}", response_model=CampaignDetailResponse)
async def get_campaign_detail(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Xem chi tiết chiến dịch tiếp thị, các kênh phân phối, sản phẩm hero, khuyến mãi và ROI.
    """
    camp = await CampaignService.get_by_id(db, campaign_id)
    return CampaignService.format_detail_response(camp)


@router.put("/{campaign_id}", response_model=CampaignDetailResponse)
async def update_campaign(
    campaign_id: str,
    payload: CampaignUpdateInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("campaign.create")),
):
    """
    Chỉnh sửa thông tin chiến dịch, kênh phân phối và sản phẩm.
    Yêu cầu quyền campaign.create.
    """
    camp = await CampaignService.update_campaign(
        db=db,
        campaign_id=campaign_id,
        data=payload,
    )
    return CampaignService.format_detail_response(camp)


@router.post("/{campaign_id}/submit-review", response_model=CampaignDetailResponse)
async def submit_for_review(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("campaign.create")),
):
    """
    Gửi duyệt kế hoạch và ngân sách chiến dịch (DRAFT -> READY_FOR_REVIEW).
    """
    camp = await CampaignService.submit_for_review(db=db, campaign_id=campaign_id)
    return CampaignService.format_detail_response(camp)


@router.post("/{campaign_id}/approve", response_model=CampaignDetailResponse)
async def approve_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("campaign.approve")),
):
    """
    Phê duyệt chiến dịch tiếp thị và hạn mức ngân sách (READY_FOR_REVIEW -> APPROVED).
    Yêu cầu quyền campaign.approve (Admin / Owner / Trưởng bộ phận Marketing).
    """
    camp = await CampaignService.approve_campaign(
        db=db,
        campaign_id=campaign_id,
        user_id=current_user.id,
    )
    return CampaignService.format_detail_response(camp)


@router.post("/{campaign_id}/status", response_model=CampaignDetailResponse)
async def update_campaign_status(
    campaign_id: str,
    payload: CampaignStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("campaign.create")),
):
    """
    Cập nhật trạng thái chiến dịch: ACTIVE, PAUSED, COMPLETED, CANCELLED.
    """
    camp = await CampaignService.update_status(
        db=db,
        campaign_id=campaign_id,
        new_status=payload.status,
    )
    return CampaignService.format_detail_response(camp)


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("campaign.create")),
):
    """
    Xóa chiến dịch (chỉ cho phép khi ở trạng thái Bản nháp, Chờ duyệt, hoặc Hủy).
    """
    await CampaignService.delete_campaign(db=db, campaign_id=campaign_id)
    return {"message": "Đã xóa chiến dịch thành công"}
