from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, require_permission
from app.models.auth import User
from app.schemas.recommendation import (
    SmartAlertResponse,
    SmartAlertListResponse,
    SmartAlertSummaryResponse,
)
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/alerts", tags=["Smart Alerts & Operational Warnings"])


@router.get("/summary", response_model=SmartAlertSummaryResponse)
async def get_alerts_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lấy tổng hợp cảnh báo (critical, warning, info, total_active) và 5 cảnh báo gần nhất
    cho Notification Bell và Dashboard Widget.
    """
    return await RecommendationService.get_alerts_summary(db)


@router.get("", response_model=SmartAlertListResponse)
async def list_alerts(
    severity: Optional[str] = Query(None, description="Lọc theo mức độ nghiêm trọng (CRITICAL, WARNING, INFO)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Lọc theo trạng thái (ACTIVE, ACKNOWLEDGED, RESOLVED)"),
    entity_type: Optional[str] = Query(None, description="Lọc theo đối tượng (PRODUCT, INVENTORY_BATCH, CAMPAIGN, CHANNEL)"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Danh sách các cảnh báo thông minh thời gian thực.
    """
    skip = (page - 1) * limit
    items = await RecommendationService.get_alerts(
        db=db,
        severity=severity,
        status=status_filter,
        entity_type=entity_type,
        skip=skip,
        limit=limit,
    )
    total = await RecommendationService.get_alerts_count(
        db=db,
        severity=severity,
        status=status_filter,
        entity_type=entity_type,
    )
    return SmartAlertListResponse(items=items, total=total)


@router.post("/scan", response_model=list[SmartAlertResponse])
async def trigger_alerts_scan(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("inventory.read")),
):
    """
    Kích hoạt quét toàn bộ hệ thống để phát hiện các rủi ro vận hành (cận date, cạn kho, biên sàn).
    """
    return await RecommendationService.scan_and_generate_alerts(db)


@router.post("/{alert_id}/acknowledge", response_model=SmartAlertResponse)
async def acknowledge_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Đánh dấu cảnh báo đã được nhân sự xem qua (Acknowledged).
    """
    try:
        return await RecommendationService.acknowledge_alert(
            db=db, alert_id=alert_id, user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{alert_id}/resolve", response_model=SmartAlertResponse)
async def resolve_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Đánh dấu đã giải quyết xong cảnh báo (Resolved).
    """
    try:
        return await RecommendationService.resolve_alert(
            db=db, alert_id=alert_id, user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
