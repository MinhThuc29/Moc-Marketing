from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.analytics import (
    TrackingEventCreate,
    TrackingBatchCreate,
    TrackingEventResponse,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/tracking", tags=["Tracking"])


@router.post(
    "/events",
    response_model=TrackingEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ghi nhận sự kiện tracking (Public clickstream endpoint)",
)
async def record_tracking_event(
    payload: TrackingEventCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Public ingestion endpoint for client-side events:
    page_view, product_view, add_to_cart, begin_checkout, purchase, campaign_click, outbound_click.
    """
    return await AnalyticsService.record_event(db, payload)


@router.post(
    "/batch",
    status_code=status.HTTP_201_CREATED,
    summary="Ghi nhận danh sách sự kiện theo lô (Batch ingestion)",
)
async def record_batch_tracking_events(
    payload: TrackingBatchCreate,
    db: AsyncSession = Depends(get_db),
):
    """Batch ingestion endpoint to record multiple tracking events simultaneously."""
    count = await AnalyticsService.record_batch_events(db, payload.events)
    return {"status": "success", "recorded_count": count}
