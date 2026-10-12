from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, require_permission
from app.models.auth import User
from app.schemas.recommendation import (
    RecommendationResponse,
    RecommendationListResponse,
    RecommendationOverviewStats,
    ConvertCampaignRequest,
    ConvertWorkflowRequest,
    DismissRecommendationRequest,
    GenerateRecommendationsRequest,
)
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["AI Recommendation Engine & Strategist"])


@router.get("/overview", response_model=RecommendationOverviewStats)
async def get_recommendation_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Thống kê tổng quan đề xuất AI và cảnh báo thông minh:
    Tổng đề xuất, chờ duyệt (pending), đã áp dụng (applied), độ tin cậy cao, số lượng cảnh báo active/critical.
    """
    return await RecommendationService.get_overview_stats(db)


@router.get("", response_model=RecommendationListResponse)
async def list_recommendations(
    status_filter: Optional[str] = Query(None, alias="status", description="Lọc theo trạng thái (PENDING, APPLIED, DISMISSED)"),
    rec_type: Optional[str] = Query(None, alias="type", description="Lọc theo loại khuyến nghị"),
    confidence: Optional[str] = Query(None, description="Lọc theo mức độ tin cậy (HIGH, MEDIUM, LOW)"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Danh sách các khuyến nghị AI được sắp xếp theo độ tin cậy và thời gian tạo mới nhất.
    """
    skip = (page - 1) * limit
    items = await RecommendationService.get_recommendations(
        db=db,
        status=status_filter,
        rec_type=rec_type,
        confidence=confidence,
        skip=skip,
        limit=limit,
    )
    total = await RecommendationService.get_recommendations_count(
        db=db,
        status=status_filter,
        rec_type=rec_type,
        confidence=confidence,
    )
    return RecommendationListResponse(
        items=items,
        total=total,
        page=page,
        page_size=limit,
    )


@router.get("/{rec_id}", response_model=RecommendationResponse)
async def get_recommendation_detail(
    rec_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Chi tiết một khuyến nghị AI kèm các bằng chứng số học (evidence array) và rủi ro.
    """
    rec = await RecommendationService.get_recommendation_by_id(db, rec_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy đề xuất AI với ID {rec_id}",
        )
    return rec


@router.post("/generate", response_model=list[RecommendationResponse])
async def generate_recommendations(
    payload: GenerateRecommendationsRequest = GenerateRecommendationsRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("content.create")),
):
    """
    Kích hoạt AI Marketing Strategist quét toàn bộ DB (kho hàng, đơn hàng, khách hàng)
    và sinh các đề xuất mới có bằng chứng dữ liệu thực tế.
    """
    recs = await RecommendationService.scan_and_generate_recommendations(
        db=db, force_regenerate=payload.force_regenerate
    )
    return recs


@router.post("/{rec_id}/convert-to-campaign")
async def convert_recommendation_to_campaign(
    rec_id: str,
    payload: ConvertCampaignRequest = ConvertCampaignRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("campaign.create")),
):
    """
    1-Click Convert: Chuyển đổi đề xuất AI thành Bản nháp chiến dịch tiếp thị (Campaign Draft).
    """
    try:
        campaign = await RecommendationService.convert_to_campaign(
            db=db,
            rec_id=rec_id,
            user_id=current_user.id,
            custom_name=payload.custom_name,
            budget=payload.budget,
        )
        return {
            "success": True,
            "message": "Đã chuyển đổi đề xuất thành bản nháp chiến dịch tiếp thị thành công!",
            "campaign_id": campaign.id,
            "campaign_code": campaign.code,
            "campaign_name": campaign.name,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{rec_id}/convert-to-automation")
async def convert_recommendation_to_automation(
    rec_id: str,
    payload: ConvertWorkflowRequest = ConvertWorkflowRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("settings.manage")),
):
    """
    1-Click Convert: Chuyển đổi đề xuất AI thành Kịch bản Tự động hóa tiếp thị (Automation Workflow).
    """
    try:
        workflow = await RecommendationService.convert_to_automation_workflow(
            db=db,
            rec_id=rec_id,
            user_id=current_user.id,
            custom_name=payload.custom_name,
        )
        return {
            "success": True,
            "message": "Đã chuyển đổi đề xuất thành kịch bản tự động hóa tiếp thị thành công!",
            "workflow_id": workflow.id,
            "workflow_code": workflow.code,
            "workflow_name": workflow.name,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{rec_id}/dismiss", response_model=RecommendationResponse)
async def dismiss_recommendation(
    rec_id: str,
    payload: DismissRecommendationRequest = DismissRecommendationRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("content.create")),
):
    """
    Bỏ qua đề xuất AI không muốn áp dụng kèm lý do tùy chọn.
    """
    try:
        rec = await RecommendationService.dismiss_recommendation(
            db=db, rec_id=rec_id, reason=payload.reason
        )
        return rec
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
