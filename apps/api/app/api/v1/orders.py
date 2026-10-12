from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import require_permission, get_current_user
from app.models.auth import User
from app.schemas.order import (
    OrderStatusUpdateRequest,
    OrderPaymentStatusUpdateRequest,
    OrderInternalNoteUpdateRequest,
    ManualOrderCreateRequest,
    AdminOrderListResponse,
    AdminOrderDetailResponse,
    OrderOverviewStatsResponse,
    OrderTrackingRequest,
    OrderTrackingResponse,
)
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Order Management (Admin & Tracking)"])


@router.get("/overview", response_model=OrderOverviewStatsResponse)
async def get_orders_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("order.read")),
):
    """
    Get high-level order overview statistics for admin dashboard.
    Requires order.read permission.
    """
    return await OrderService.get_overview_stats(db=db)


@router.get("", response_model=AdminOrderListResponse)
async def list_orders(
    search: Optional[str] = Query(None, description="Tìm theo mã đơn, tên hoặc số điện thoại"),
    status: Optional[str] = Query(None, description="Lọc theo trạng thái đơn"),
    payment_status: Optional[str] = Query(None, description="Lọc theo trạng thái thanh toán"),
    payment_method: Optional[str] = Query(None, description="Lọc theo phương thức thanh toán"),
    source: Optional[str] = Query(None, description="Lọc theo nguồn đơn hàng"),
    from_date: Optional[datetime] = Query(None, description="Từ ngày"),
    to_date: Optional[datetime] = Query(None, description="Đến ngày"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("order.read")),
):
    """
    List orders with filtering, search and pagination for Admin.
    Requires order.read permission.
    """
    return await OrderService.list_orders(
        db=db,
        search=search,
        status_filter=status,
        payment_status=payment_status,
        payment_method=payment_method,
        source=source,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )


@router.get("/{order_id}", response_model=AdminOrderDetailResponse)
async def get_order_detail(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("order.read")),
):
    """
    Get full order details with line items and status transition timeline.
    Requires order.read permission.
    """
    return await OrderService.get_order_detail(db=db, order_id=order_id)


@router.post("", response_model=AdminOrderDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_manual_order(
    payload: ManualOrderCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("order.update")),
):
    """
    Create a manual order at counter or via phone call by staff/admin.
    Requires order.update permission.
    """
    return await OrderService.create_manual_order(
        db=db,
        req=payload,
        user_id=current_user.id,
    )


@router.patch("/{order_id}/status", response_model=AdminOrderDetailResponse)
async def update_order_status(
    order_id: str,
    payload: OrderStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("order.update")),
):
    """
    Update order lifecycle status according to valid state machine transitions.
    Requires order.update permission.
    """
    return await OrderService.update_status(
        db=db,
        order_id=order_id,
        req=payload,
        user_id=current_user.id,
    )


@router.patch("/{order_id}/payment-status", response_model=AdminOrderDetailResponse)
async def update_payment_status(
    order_id: str,
    payload: OrderPaymentStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("order.update")),
):
    """
    Update order payment status (e.g. mark as PAID after verifying bank transfer).
    Requires order.update permission.
    """
    return await OrderService.update_payment_status(
        db=db,
        order_id=order_id,
        req=payload,
        user_id=current_user.id,
    )


@router.patch("/{order_id}/internal-note", response_model=AdminOrderDetailResponse)
async def update_internal_note(
    order_id: str,
    payload: OrderInternalNoteUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("order.update")),
):
    """
    Update staff internal note for an order.
    Requires order.update permission.
    """
    return await OrderService.update_internal_note(
        db=db,
        order_id=order_id,
        req=payload,
        user_id=current_user.id,
    )


@router.post("/tracking", response_model=OrderTrackingResponse)
async def track_order_public(
    payload: OrderTrackingRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Public customer order tracking endpoint.
    No authentication required.
    """
    return await OrderService.track_order_public(
        db=db,
        order_number=payload.order_number,
        phone=payload.phone,
    )
