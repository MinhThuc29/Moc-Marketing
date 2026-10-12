from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.deps import get_current_user, require_permission
from app.models.auth import User
from app.models.order import Order
from app.models.analytics import ConversionAttribution
from app.schemas.analytics import (
    AnalyticsDashboardResponse,
    ChannelAnalyticsItem,
    CampaignAttributionComparison,
    FunnelStepItem,
    ConversionAttributionResponse,
)
from app.services.analytics_service import AnalyticsService
from app.services.attribution_service import AttributionService

router = APIRouter(prefix="/analytics", tags=["Marketing Analytics & Attribution Engine"])


@router.get(
    "/overview",
    response_model=AnalyticsDashboardResponse,
    summary="Báo cáo tổng quan Marketing KPIs, Đa kênh, Phân bổ Attribution và Phễu chuyển đổi",
)
async def get_analytics_overview(
    period: str = Query("30d", description="Khoảng thời gian: 7d, 30d, 90d"),
    start_date: Optional[datetime] = Query(None, description="Ngày bắt đầu (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Ngày kết thúc (ISO format)"),
    current_user: User = Depends(require_permission("analytics.read")),
    db: AsyncSession = Depends(get_db),
):
    """
    Get comprehensive CEO & Marketing Analytics Dashboard:
    - KPIs: Gross vs Net revenue, Attributed revenue, Marketing spend, ROAS, MER, CAC, LTV, LTV/CAC ratio.
    - Omnichannel channel breakdown: Website, GrabFood, ShopeeFood, Zalo, Facebook, Offline.
    - Campaign attribution models: First-Touch vs Last-Touch vs Linear comparison.
    - 5-step conversion funnel: Page View -> Product View -> Add to Cart -> Checkout -> Purchase.
    - AI Marketing Insights with actionable recommendations.
    """
    return await AnalyticsService.get_analytics_dashboard(
        db=db,
        start_date=start_date,
        end_date=end_date,
        period=period,
    )


@router.get(
    "/channels",
    response_model=List[ChannelAnalyticsItem],
    summary="Báo cáo chi tiết P&L phân bổ theo kênh bán hàng",
)
async def get_channel_analytics(
    period: str = Query("30d"),
    current_user: User = Depends(require_permission("analytics.read")),
    db: AsyncSession = Depends(get_db),
):
    dash = await AnalyticsService.get_analytics_dashboard(db=db, period=period)
    return dash.channel_breakdown


@router.get(
    "/campaigns",
    response_model=List[CampaignAttributionComparison],
    summary="So sánh hiệu quả phân bổ chiến dịch đa mô hình (First-Touch vs Last-Touch vs Linear)",
)
async def get_campaign_attributions(
    period: str = Query("30d"),
    current_user: User = Depends(require_permission("analytics.read")),
    db: AsyncSession = Depends(get_db),
):
    dash = await AnalyticsService.get_analytics_dashboard(db=db, period=period)
    return dash.campaign_attributions


@router.get(
    "/funnel",
    response_model=List[FunnelStepItem],
    summary="Phễu chuyển đổi hành vi khách hàng",
)
async def get_conversion_funnel(
    period: str = Query("30d"),
    current_user: User = Depends(require_permission("analytics.read")),
    db: AsyncSession = Depends(get_db),
):
    dash = await AnalyticsService.get_analytics_dashboard(db=db, period=period)
    return dash.funnel


@router.get(
    "/orders/{order_id}/attribution",
    response_model=List[ConversionAttributionResponse],
    summary="Lấy chi tiết phân bổ điểm chạm tiếp thị cho một đơn hàng cụ thể",
)
async def get_order_attribution(
    order_id: str,
    current_user: User = Depends(require_permission("analytics.read")),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(ConversionAttribution).where(ConversionAttribution.order_id == order_id)
    )
    items = res.scalars().all()
    if not items:
        # If not computed yet, compute on the fly
        order_res = await db.execute(select(Order).where(Order.id == order_id))
        order = order_res.scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy đơn hàng")
        items = await AttributionService.compute_order_attribution(db, order)
    return items


@router.post(
    "/orders/{order_id}/compute-attribution",
    response_model=List[ConversionAttributionResponse],
    summary="Tính toán hoặc tính lại phân bổ tiếp thị cho một đơn hàng",
)
async def compute_order_attribution(
    order_id: str,
    current_user: User = Depends(require_permission("analytics.read")),
    db: AsyncSession = Depends(get_db),
):
    order_res = await db.execute(select(Order).where(Order.id == order_id))
    order = order_res.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy đơn hàng")

    return await AttributionService.compute_order_attribution(db, order)
