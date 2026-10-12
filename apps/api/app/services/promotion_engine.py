from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.promotion import (
    Promotion,
    PromotionUsage,
    PromotionType,
    PromotionStatus,
    ProductScope,
    CustomerScope,
)
from app.schemas.promotion import (
    CartItemInput,
    CalculationRequest,
    CalculationResponse,
    AppliedPromotionItem,
    FreeGiftItem,
    PromotionCreateRequest,
    PromotionUpdateRequest,
    PromotionResponse,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_promotion_response(p: Promotion, now: Optional[datetime] = None) -> PromotionResponse:
    if now is None:
        now = utc_now()
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    start = p.start_at
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)

    end = p.end_at
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)

    is_valid_now = (
        p.status == PromotionStatus.ACTIVE.value
        and start <= now <= end
        and (p.usage_limit is None or p.usage_count < p.usage_limit)
    )

    return PromotionResponse(
        id=p.id,
        title=p.title,
        code=p.code,
        description=p.description,
        type=p.type,
        value=float(p.value),
        min_order_value=float(p.min_order_value) if p.min_order_value is not None else None,
        max_discount=float(p.max_discount) if p.max_discount is not None else None,
        start_at=p.start_at,
        end_at=p.end_at,
        product_scope=p.product_scope,
        applicable_product_ids=p.applicable_product_ids or [],
        applicable_category_ids=p.applicable_category_ids or [],
        buy_x_get_y_config=p.buy_x_get_y_config,
        combo_config=p.combo_config,
        customer_scope=p.customer_scope,
        usage_limit=p.usage_limit,
        usage_count=p.usage_count,
        usage_per_customer=p.usage_per_customer,
        stackable=p.stackable,
        status=p.status,
        created_at=p.created_at,
        updated_at=p.updated_at,
        is_valid_now=is_valid_now,
    )


class PromotionEngine:
    """
    Pure promotion calculation service (Backend Authoritative & Deterministic).
    Client never submits final prices - backend strictly calculates discounts.
    """

    @staticmethod
    def is_item_in_scope(item: CartItemInput, promo: Promotion) -> bool:
        if promo.product_scope == ProductScope.ALL.value:
            return True
        if promo.product_scope == ProductScope.SPECIFIC_PRODUCTS.value:
            return item.product_id in (promo.applicable_product_ids or [])
        if promo.product_scope == ProductScope.SPECIFIC_CATEGORIES.value:
            return bool(item.category_id and item.category_id in (promo.applicable_category_ids or []))
        return True

    @staticmethod
    async def evaluate_promotion(
        db: AsyncSession,
        promo: Promotion,
        items: List[CartItemInput],
        shipping_fee: float,
        subtotal: float,
        user_id: Optional[str],
        is_new_customer: bool,
        as_of: datetime,
    ) -> Tuple[bool, Optional[str], float, float, List[FreeGiftItem]]:
        """
        Evaluates a single promotion against cart items.
        Returns: (is_eligible, rejection_reason, discount_amount, shipping_discount, free_items)
        """
        # 1. Status check
        if promo.status != PromotionStatus.ACTIVE.value:
            return False, f"Chương trình '{promo.title}' hiện đang tạm dừng hoặc không hoạt động.", 0.0, 0.0, []

        # 2. Timing check
        start = promo.start_at.replace(tzinfo=timezone.utc) if promo.start_at.tzinfo is None else promo.start_at
        end = promo.end_at.replace(tzinfo=timezone.utc) if promo.end_at.tzinfo is None else promo.end_at

        if as_of < start:
            return False, f"Chương trình '{promo.title}' chưa bắt đầu (bắt đầu lúc {start.strftime('%d/%m/%Y %H:%M')}).", 0.0, 0.0, []
        if as_of > end:
            return False, f"Chương trình '{promo.title}' đã kết thúc.", 0.0, 0.0, []

        # 3. Global usage limit
        if promo.usage_limit is not None and promo.usage_count >= promo.usage_limit:
            return False, f"Mã '{promo.code or promo.title}' đã hết lượt sử dụng.", 0.0, 0.0, []

        # 4. Usage per customer
        if user_id and promo.usage_per_customer is not None:
            stmt_user_usage = select(func.count(PromotionUsage.id)).where(
                PromotionUsage.promotion_id == promo.id,
                PromotionUsage.user_id == user_id,
            )
            res_user_usage = await db.execute(stmt_user_usage)
            user_count = res_user_usage.scalar() or 0
            if user_count >= promo.usage_per_customer:
                return False, f"Bạn đã sử dụng hết số lần quy định cho mã này ({promo.usage_per_customer} lần).", 0.0, 0.0, []

        # 5. Customer scope
        if promo.customer_scope == CustomerScope.NEW_CUSTOMER.value and not is_new_customer:
            return False, "Khuyến mãi chỉ áp dụng cho đơn hàng đầu tiên của khách hàng mới.", 0.0, 0.0, []

        # 6. Min order value
        if promo.min_order_value is not None and subtotal < float(promo.min_order_value):
            min_val = float(promo.min_order_value)
            return False, f"Đơn hàng cần đạt tối thiểu {min_val:,.0f} đ để áp dụng mã '{promo.code or promo.title}'.", 0.0, 0.0, []

        # 7. Product scope check
        matching_items = [item for item in items if PromotionEngine.is_item_in_scope(item, promo)]
        if promo.product_scope != ProductScope.ALL.value and not matching_items:
            return False, "Không có sản phẩm nào trong giỏ hàng thuộc phạm vi áp dụng của chương trình này.", 0.0, 0.0, []

        # 8. Calculate discount by promotion type
        discount_amount = 0.0
        shipping_discount = 0.0
        free_items: List[FreeGiftItem] = []
        val = float(promo.value)
        max_disc = float(promo.max_discount) if promo.max_discount is not None else None

        p_type = promo.type

        if p_type in [PromotionType.PERCENT_DISCOUNT.value, PromotionType.FLASH_SALE.value]:
            eligible_subtotal = sum(i.quantity * i.unit_price for i in matching_items)
            raw = eligible_subtotal * (val / 100.0)
            discount_amount = min(raw, max_disc) if max_disc is not None else raw

        elif p_type == PromotionType.FIXED_DISCOUNT.value:
            discount_amount = min(val, subtotal)

        elif p_type == PromotionType.FREE_SHIPPING.value:
            allowance = max_disc if max_disc is not None else val
            shipping_discount = min(shipping_fee, allowance)

        elif p_type == PromotionType.VOUCHER.value:
            if val <= 100:  # treated as % voucher
                raw = subtotal * (val / 100.0)
                discount_amount = min(raw, max_disc) if max_disc is not None else raw
            else:  # fixed voucher
                discount_amount = min(val, subtotal)

        elif p_type == PromotionType.BUY_X_GET_Y.value:
            cfg = promo.buy_x_get_y_config or {}
            buy_qty = int(cfg.get("buy_quantity", 2))
            get_qty = int(cfg.get("get_quantity", 1))

            for item in matching_items:
                if item.quantity >= buy_qty:
                    sets = item.quantity // buy_qty
                    gift_qty = sets * get_qty
                    item_gift_val = gift_qty * item.unit_price
                    discount_amount += item_gift_val
                    free_items.append(
                        FreeGiftItem(
                            product_id=item.product_id,
                            product_name=item.name or "Sản phẩm tặng kèm",
                            quantity=gift_qty,
                            reason=f"Tặng theo chương trình Mua {buy_qty} Tặng {get_qty}",
                        )
                    )

        elif p_type == PromotionType.COMBO.value:
            cfg = promo.combo_config or {}
            req_ids = set(cfg.get("required_product_ids", []))
            combo_discount = float(cfg.get("combo_discount", val))

            if req_ids:
                cart_prod_map = {i.product_id: i.quantity for i in items}
                if req_ids.issubset(cart_prod_map.keys()):
                    sets = min(cart_prod_map[pid] for pid in req_ids)
                    discount_amount = sets * combo_discount

        # Discount cannot exceed subtotal
        discount_amount = min(discount_amount, subtotal)

        return True, None, round(discount_amount, 2), round(shipping_discount, 2), free_items

    @staticmethod
    async def calculate(
        db: AsyncSession,
        req: CalculationRequest,
        user_id: Optional[str] = None,
    ) -> CalculationResponse:
        as_of = req.as_of or utc_now()
        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=timezone.utc)

        subtotal = round(sum(i.quantity * i.unit_price for i in req.items), 2)
        shipping_fee = round(req.shipping_fee, 2)

        rejection_reasons: List[str] = []
        applied_promos: List[AppliedPromotionItem] = []
        all_free_items: List[FreeGiftItem] = []
        is_code_valid = False

        total_order_discount = 0.0
        total_shipping_discount = 0.0

        # 1. Process entered promo_code if any
        if req.promo_code and req.promo_code.strip():
            code = req.promo_code.strip().upper()
            res_code = await db.execute(select(Promotion).where(Promotion.code == code))
            promo_code_obj = res_code.scalar_one_or_none()

            if not promo_code_obj:
                rejection_reasons.append(f"Mã khuyến mãi '{code}' không tồn tại trong hệ thống.")
            else:
                ok, reason, disc, ship_disc, gifts = await PromotionEngine.evaluate_promotion(
                    db=db,
                    promo=promo_code_obj,
                    items=req.items,
                    shipping_fee=shipping_fee,
                    subtotal=subtotal,
                    user_id=user_id,
                    is_new_customer=req.is_new_customer,
                    as_of=as_of,
                )
                if not ok:
                    rejection_reasons.append(reason or "Mã không hợp lệ.")
                else:
                    is_code_valid = True
                    total_order_discount += disc
                    total_shipping_discount += ship_disc
                    all_free_items.extend(gifts)
                    applied_promos.append(
                        AppliedPromotionItem(
                            promotion_id=promo_code_obj.id,
                            title=promo_code_obj.title,
                            code=promo_code_obj.code,
                            type=promo_code_obj.type,
                            discount_amount=disc if disc > 0 else ship_disc,
                            description=f"Áp dụng thành công mã {code}",
                        )
                    )

        # 2. Check for auto-applied promotions without code (e.g. FLASH_SALE, COMBO, auto BUY_X_GET_Y)
        stmt_auto = select(Promotion).where(
            Promotion.status == PromotionStatus.ACTIVE.value,
            Promotion.code.is_(None),
            Promotion.start_at <= as_of,
            Promotion.end_at >= as_of,
        )
        res_auto = await db.execute(stmt_auto)
        auto_promos = list(res_auto.scalars().all())

        for p in auto_promos:
            # If a non-stackable promo is already applied, skip further non-stackable
            if applied_promos and not p.stackable:
                continue

            ok, _, disc, ship_disc, gifts = await PromotionEngine.evaluate_promotion(
                db=db,
                promo=p,
                items=req.items,
                shipping_fee=shipping_fee,
                subtotal=subtotal,
                user_id=user_id,
                is_new_customer=req.is_new_customer,
                as_of=as_of,
            )
            if ok and (disc > 0 or ship_disc > 0 or gifts):
                total_order_discount += disc
                total_shipping_discount += ship_disc
                all_free_items.extend(gifts)
                applied_promos.append(
                    AppliedPromotionItem(
                        promotion_id=p.id,
                        title=p.title,
                        code=None,
                        type=p.type,
                        discount_amount=disc if disc > 0 else ship_disc,
                        description="Khuyến mãi tự động áp dụng",
                    )
                )

        # Cap discounts
        total_order_discount = min(total_order_discount, subtotal)
        total_shipping_discount = min(total_shipping_discount, shipping_fee)
        final_total = max(0.0, subtotal - total_order_discount) + max(0.0, shipping_fee - total_shipping_discount)

        return CalculationResponse(
            subtotal=subtotal,
            discount_amount=round(total_order_discount, 2),
            shipping_fee=shipping_fee,
            shipping_discount=round(total_shipping_discount, 2),
            final_total=round(final_total, 2),
            applied_promotions=applied_promos,
            free_items=all_free_items,
            rejection_reasons=rejection_reasons,
            is_code_valid=is_code_valid,
        )
