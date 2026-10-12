from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.order import Order
from app.schemas.checkout import (
    CheckoutRequest,
    CheckoutResponse,
)
from app.services.checkout_service import CheckoutService

router = APIRouter(prefix="/checkout", tags=["Checkout (Storefront)"])


@router.post("", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
async def checkout_order(
    payload: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit customer order with server-side authoritative calculations.
    Guarantees stock availability, validates voucher, deducts inventory via FEFO,
    and returns payment / transfer instructions.
    """
    return await CheckoutService.process_checkout(db=db, req=payload)


@router.get("/orders/{order_number}", response_model=CheckoutResponse)
async def get_order_by_number(
    order_number: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Public lookup for order confirmation and tracking details by order number.
    """
    stmt = (
        select(Order)
        .where(Order.order_number == order_number.strip().upper())
        .options(selectinload(Order.items))
    )
    res = await db.execute(stmt)
    order = res.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy đơn hàng với mã '{order_number}'.",
        )

    return CheckoutService._format_order_response(order)
