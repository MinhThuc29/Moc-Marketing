import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.cart import Cart, CartItem, CartStatus
from app.models.product import Product, ProductStatus
from app.models.inventory import InventoryBatch, BatchStatus
from app.models.promotion import Promotion, PromotionStatus
from app.schemas.cart import (
    CartItemResponse,
    CartResponse,
    CartValidationIssue,
    CartValidationResponse,
)
from app.schemas.promotion import CartItemInput, FreeGiftItem
from app.services.promotion_engine import PromotionEngine


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CartService:
    STANDARD_SHIPPING_FEE = 25000.0  # 25.000 VND standard delivery fee
    FREE_SHIPPING_THRESHOLD = 120000.0  # Free shipping for orders >= 120.000 VND

    @staticmethod
    async def get_or_create_cart(
        db: AsyncSession,
        cart_token: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Cart:
        now = utc_now()
        cart: Optional[Cart] = None

        if cart_token and cart_token.strip():
            stmt = (
                select(Cart)
                .where(
                    and_(
                        Cart.cart_token == cart_token.strip(),
                        Cart.status == CartStatus.ACTIVE.value,
                    )
                )
                .options(selectinload(Cart.items).selectinload(CartItem.product))
            )
            res = await db.execute(stmt)
            cart = res.scalar_one_or_none()

            # Check if cart is expired
            if cart:
                expiry = cart.expires_at.replace(tzinfo=timezone.utc) if cart.expires_at.tzinfo is None else cart.expires_at
                if expiry < now:
                    cart.status = CartStatus.EXPIRED.value
                    cart = None

        if not cart:
            new_token = cart_token.strip() if cart_token and len(cart_token.strip()) >= 10 else f"cart_{uuid.uuid4().hex}"
            cart = Cart(
                cart_token=new_token,
                user_id=user_id,
                status=CartStatus.ACTIVE.value,
                expires_at=now + timedelta(days=14),
                created_at=now,
                updated_at=now,
            )
            db.add(cart)
            await db.commit()
            await db.refresh(cart)

            # Reload with items
            stmt = (
                select(Cart)
                .where(Cart.id == cart.id)
                .options(selectinload(Cart.items).selectinload(CartItem.product))
            )
            res = await db.execute(stmt)
            cart = res.scalar_one()
        elif user_id and cart.user_id != user_id:
            cart.user_id = user_id
            cart.updated_at = now
            await db.commit()

        return cart

    @staticmethod
    async def add_item(
        db: AsyncSession,
        cart_token: str,
        product_id: str,
        quantity: int = 1,
        note: Optional[str] = None,
    ) -> Cart:
        cart = await CartService.get_or_create_cart(db, cart_token)

        # 1. Verify product exists & is ACTIVE
        res_p = await db.execute(select(Product).where(Product.id == product_id))
        product = res_p.scalar_one_or_none()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy sản phẩm có mã {product_id}.",
            )
        if product.status != ProductStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sản phẩm '{product.name}' hiện không sẵn sàng để đặt hàng ({product.status}).",
            )

        now = utc_now()
        # 2. Check if item already exists in cart
        existing_item = next((it for it in cart.items if it.product_id == product_id), None)
        if existing_item:
            existing_item.quantity += quantity
            if note is not None:
                existing_item.note = note
            existing_item.updated_at = now
        else:
            new_item = CartItem(
                cart_id=cart.id,
                product_id=product.id,
                quantity=quantity,
                note=note,
                created_at=now,
                updated_at=now,
            )
            db.add(new_item)
            cart.items.append(new_item)

        cart.updated_at = now
        await db.commit()

        # Reload with populate_existing=True
        stmt = (
            select(Cart)
            .where(Cart.id == cart.id)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
            .execution_options(populate_existing=True)
        )
        res = await db.execute(stmt)
        return res.scalar_one()

    @staticmethod
    async def _is_new_customer(db: AsyncSession, user_id: Optional[str]) -> bool:
        if not user_id:
            return True
        from app.models.order import Order
        res = await db.execute(select(func.count(Order.id)).where(Order.user_id == user_id))
        order_count = res.scalar() or 0
        return order_count == 0

    @staticmethod
    async def update_item(
        db: AsyncSession,
        cart_token: str,
        item_id: str,
        quantity: int,
        note: Optional[str] = None,
    ) -> Cart:
        cart = await CartService.get_or_create_cart(db, cart_token)
        target_item = next((it for it in cart.items if it.id == item_id), None)
        if not target_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mục sản phẩm không tồn tại trong giỏ hàng.",
            )

        now = utc_now()
        if quantity <= 0:
            cart.items = [it for it in cart.items if it.id != item_id]
            await db.delete(target_item)
        else:
            target_item.quantity = quantity
            if note is not None:
                target_item.note = note
            target_item.updated_at = now

        cart.updated_at = now
        await db.commit()

        # Reload
        stmt = (
            select(Cart)
            .where(Cart.id == cart.id)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
            .execution_options(populate_existing=True)
        )
        res = await db.execute(stmt)
        return res.scalar_one()

    @staticmethod
    async def remove_item(
        db: AsyncSession,
        cart_token: str,
        item_id: str,
    ) -> Cart:
        cart = await CartService.get_or_create_cart(db, cart_token)
        target_item = next((it for it in cart.items if it.id == item_id), None)
        if not target_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mục sản phẩm không tồn tại trong giỏ hàng.",
            )

        cart.items = [it for it in cart.items if it.id != item_id]
        await db.delete(target_item)
        cart.updated_at = utc_now()
        await db.commit()

        # Reload
        stmt = (
            select(Cart)
            .where(Cart.id == cart.id)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
            .execution_options(populate_existing=True)
        )
        res = await db.execute(stmt)
        return res.scalar_one()

    @staticmethod
    async def clear_cart(
        db: AsyncSession,
        cart_token: str,
    ) -> Cart:
        cart = await CartService.get_or_create_cart(db, cart_token)
        for item in list(cart.items):
            await db.delete(item)
        cart.items = []
        cart.promo_code = None
        cart.updated_at = utc_now()
        await db.commit()

        # Reload
        stmt = (
            select(Cart)
            .where(Cart.id == cart.id)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
            .execution_options(populate_existing=True)
        )
        res = await db.execute(stmt)
        return res.scalar_one()

    @staticmethod
    async def apply_coupon(
        db: AsyncSession,
        cart_token: str,
        code: str,
    ) -> Cart:
        cart = await CartService.get_or_create_cart(db, cart_token)
        clean_code = code.strip().upper()

        # Check if promo exists
        stmt = select(Promotion).where(Promotion.code == clean_code)
        res = await db.execute(stmt)
        promo = res.scalar_one_or_none()
        if not promo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mã ưu đãi '{clean_code}' không tồn tại hoặc đã hết hiệu lực.",
            )

        # Check promotion against current cart items
        calc_items = []
        subtotal = 0.0
        for item in cart.items:
            prod = item.product
            if prod and prod.status == ProductStatus.ACTIVE.value:
                u_price = float(prod.sale_price) if (prod.sale_price and prod.sale_price > 0) else float(prod.base_price)
                calc_items.append(
                    CartItemInput(
                        product_id=prod.id,
                        category_id=prod.category_id,
                        quantity=item.quantity,
                        unit_price=u_price,
                        name=prod.name,
                    )
                )
                subtotal += u_price * item.quantity

        is_new_cust = await CartService._is_new_customer(db, cart.user_id)
        is_eligible, reason, discount, ship_discount, _ = await PromotionEngine.evaluate_promotion(
            db=db,
            promo=promo,
            items=calc_items,
            shipping_fee=CartService.STANDARD_SHIPPING_FEE,
            subtotal=subtotal,
            user_id=cart.user_id,
            is_new_customer=is_new_cust,
            as_of=utc_now(),
        )

        if not is_eligible:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=reason or f"Mã '{clean_code}' không đủ điều kiện áp dụng cho giỏ hàng hiện tại.",
            )

        cart.promo_code = clean_code
        cart.updated_at = utc_now()
        await db.commit()

        # Reload
        stmt = (
            select(Cart)
            .where(Cart.id == cart.id)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
        )
        res = await db.execute(stmt)
        return res.scalar_one()

    @staticmethod
    async def remove_coupon(
        db: AsyncSession,
        cart_token: str,
    ) -> Cart:
        cart = await CartService.get_or_create_cart(db, cart_token)
        cart.promo_code = None
        cart.updated_at = utc_now()
        await db.commit()

        # Reload
        stmt = (
            select(Cart)
            .where(Cart.id == cart.id)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
        )
        res = await db.execute(stmt)
        return res.scalar_one()

    @staticmethod
    async def get_cart_summary(
        db: AsyncSession,
        cart: Cart,
    ) -> CartResponse:
        """
        Authoritative calculation of cart totals.
        Never trusts client totals.
        Checks product status, inventory, promotions, shipping.
        """
        now = utc_now()
        item_responses: List[CartItemResponse] = []
        calc_items: List[CartItemInput] = []
        warnings: List[str] = []
        subtotal = 0.0

        for item in cart.items:
            prod = item.product
            if not prod:
                warnings.append(f"Một sản phẩm trong giỏ không còn tồn tại trên hệ thống.")
                continue

            # Check product status
            is_active = prod.status == ProductStatus.ACTIVE.value
            if not is_active:
                warnings.append(f"Sản phẩm '{prod.name}' hiện đang tạm ngừng bán.")

            # Compute authoritative prices
            base_p = float(prod.base_price)
            unit_p = float(prod.sale_price) if (prod.sale_price and prod.sale_price > 0) else base_p
            line_tot = unit_p * item.quantity

            if is_active:
                subtotal += line_tot
                calc_items.append(
                    CartItemInput(
                        product_id=prod.id,
                        category_id=prod.category_id,
                        quantity=item.quantity,
                        unit_price=unit_p,
                        name=prod.name,
                    )
                )

            item_responses.append(
                CartItemResponse(
                    id=item.id,
                    product_id=prod.id,
                    product_name=prod.name,
                    product_sku=prod.sku,
                    product_slug=prod.slug,
                    product_unit=prod.unit or "phần",
                    thumbnail=prod.thumbnail,
                    unit_price=unit_p,
                    original_price=base_p,
                    quantity=item.quantity,
                    line_total=line_tot,
                    note=item.note,
                    is_available=is_active,
                    stock_available=999,
                )
            )

        # Shipping fee rule: 25.000 VND unless subtotal >= 120.000 VND or 0 items
        shipping_fee = 0.0
        if subtotal > 0:
            if subtotal < CartService.FREE_SHIPPING_THRESHOLD:
                shipping_fee = CartService.STANDARD_SHIPPING_FEE
            else:
                shipping_fee = 0.0

        discount_amount = 0.0
        shipping_discount = 0.0
        applied_promo_title = None
        promo_message = None
        free_gifts: List[FreeGiftItem] = []

        # Validate promotion if code present
        if cart.promo_code:
            stmt = select(Promotion).where(Promotion.code == cart.promo_code)
            res = await db.execute(stmt)
            promo = res.scalar_one_or_none()
            if promo:
                is_new_cust = await CartService._is_new_customer(db, cart.user_id)
                is_eligible, reason, disc, s_disc, gifts = await PromotionEngine.evaluate_promotion(
                    db=db,
                    promo=promo,
                    items=calc_items,
                    shipping_fee=shipping_fee,
                    subtotal=subtotal,
                    user_id=cart.user_id,
                    is_new_customer=is_new_cust,
                    as_of=now,
                )
                if is_eligible:
                    discount_amount = disc
                    shipping_discount = s_disc
                    applied_promo_title = promo.title
                    free_gifts = gifts
                    promo_message = f"Áp dụng thành công mã {promo.code}: Giảm {disc:,.0f}₫"
                else:
                    warnings.append(f"Mã '{cart.promo_code}' không còn hiệu lực: {reason}")
            else:
                warnings.append(f"Mã '{cart.promo_code}' không tồn tại.")

        final_shipping = max(0.0, shipping_fee - shipping_discount)
        final_total = max(0.0, subtotal - discount_amount + final_shipping)
        total_items = sum(it.quantity for it in cart.items)

        return CartResponse(
            cart_token=cart.cart_token,
            items=item_responses,
            total_items=total_items,
            subtotal=subtotal,
            discount_amount=discount_amount,
            shipping_fee=shipping_fee,
            shipping_discount=shipping_discount,
            final_total=final_total,
            applied_promo_code=cart.promo_code,
            applied_promo_title=applied_promo_title,
            promo_message=promo_message,
            free_gifts=free_gifts,
            warnings=warnings,
        )

    @staticmethod
    async def validate_cart(
        db: AsyncSession,
        cart_token: str,
    ) -> CartValidationResponse:
        cart = await CartService.get_or_create_cart(db, cart_token)
        summary = await CartService.get_cart_summary(db, cart)

        issues: List[CartValidationIssue] = []
        for it in summary.items:
            if not it.is_available:
                issues.append(
                    CartValidationIssue(
                        product_id=it.product_id,
                        product_name=it.product_name,
                        issue_type="INACTIVE",
                        message=f"Sản phẩm '{it.product_name}' hiện không sẵn sàng.",
                    )
                )

        is_valid = len(issues) == 0 and len(summary.items) > 0
        return CartValidationResponse(
            is_valid=is_valid,
            issues=issues,
            cart=summary,
        )
