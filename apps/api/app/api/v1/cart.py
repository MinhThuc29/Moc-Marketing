from typing import Optional
from fastapi import APIRouter, Depends, Header, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.cart import (
    AddToCartRequest,
    UpdateCartItemRequest,
    ApplyCouponRequest,
    CartResponse,
    CartValidationResponse,
)
from app.services.cart_service import CartService

router = APIRouter(prefix="/cart", tags=["Cart (Storefront)"])


def get_cart_token(
    x_cart_token: Optional[str] = Header(None, alias="X-Cart-Token"),
    token: Optional[str] = Query(None),
) -> str:
    cart_token = x_cart_token or token
    if not cart_token or not cart_token.strip():
        # Fallback to an empty string, service will create a new cart
        return ""
    return cart_token.strip()


@router.get("", response_model=CartResponse)
async def get_cart(
    cart_token: str = Depends(get_cart_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve authoritative cart summary and line items.
    Creates a new cart if token doesn't exist.
    """
    cart = await CartService.get_or_create_cart(db, cart_token)
    return await CartService.get_cart_summary(db, cart)


@router.post("/items", response_model=CartResponse)
async def add_cart_item(
    payload: AddToCartRequest,
    cart_token: str = Depends(get_cart_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a product item to customer cart.
    Recalculates authoritative prices.
    """
    cart = await CartService.add_item(
        db=db,
        cart_token=cart_token,
        product_id=payload.product_id,
        quantity=payload.quantity,
        note=payload.note,
    )
    return await CartService.get_cart_summary(db, cart)


@router.put("/items/{item_id}", response_model=CartResponse)
async def update_cart_item(
    item_id: str,
    payload: UpdateCartItemRequest,
    cart_token: str = Depends(get_cart_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Update quantity or note for an item in customer cart.
    """
    if not cart_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Thiếu X-Cart-Token header.",
        )
    cart = await CartService.update_item(
        db=db,
        cart_token=cart_token,
        item_id=item_id,
        quantity=payload.quantity,
        note=payload.note,
    )
    return await CartService.get_cart_summary(db, cart)


@router.delete("/items/{item_id}", response_model=CartResponse)
async def remove_cart_item(
    item_id: str,
    cart_token: str = Depends(get_cart_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove an item from customer cart.
    """
    if not cart_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Thiếu X-Cart-Token header.",
        )
    cart = await CartService.remove_item(
        db=db,
        cart_token=cart_token,
        item_id=item_id,
    )
    return await CartService.get_cart_summary(db, cart)


@router.post("/apply-coupon", response_model=CartResponse)
async def apply_coupon(
    payload: ApplyCouponRequest,
    cart_token: str = Depends(get_cart_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Apply a promotional voucher code to customer cart.
    """
    if not cart_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Thiếu X-Cart-Token header.",
        )
    cart = await CartService.apply_coupon(
        db=db,
        cart_token=cart_token,
        code=payload.code,
    )
    return await CartService.get_cart_summary(db, cart)


@router.delete("/coupon", response_model=CartResponse)
async def remove_coupon(
    cart_token: str = Depends(get_cart_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove applied coupon code from customer cart.
    """
    if not cart_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Thiếu X-Cart-Token header.",
        )
    cart = await CartService.remove_coupon(
        db=db,
        cart_token=cart_token,
    )
    return await CartService.get_cart_summary(db, cart)


@router.post("/clear", response_model=CartResponse)
async def clear_cart(
    cart_token: str = Depends(get_cart_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Clear all items in customer cart.
    """
    if not cart_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Thiếu X-Cart-Token header.",
        )
    cart = await CartService.clear_cart(
        db=db,
        cart_token=cart_token,
    )
    return await CartService.get_cart_summary(db, cart)


@router.get("/validate", response_model=CartValidationResponse)
async def validate_cart(
    cart_token: str = Depends(get_cart_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Validate cart items and promotions before navigating to checkout.
    """
    if not cart_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Thiếu X-Cart-Token header.",
        )
    return await CartService.validate_cart(db, cart_token)
