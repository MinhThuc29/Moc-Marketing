import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.cart import Cart, CartItem, CartStatus
from app.models.order import (
    Order,
    OrderItem,
    OrderStatusHistory,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
    OrderSource,
)
from app.models.product import Product, ProductStatus
from app.models.promotion import Promotion, PromotionUsage, PromotionStatus
from app.models.inventory import InventoryBatch, BatchStatus, InventoryMovement, MovementType
from app.schemas.checkout import (
    CheckoutRequest,
    CheckoutResponse,
    OrderItemSnapshotResponse,
    BankTransferInstruction,
)
from app.schemas.promotion import CartItemInput
from app.services.cart_service import CartService
from app.services.promotion_engine import PromotionEngine
from app.services.inventory_service import InventoryService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CheckoutService:
    @staticmethod
    async def process_checkout(
        db: AsyncSession,
        req: CheckoutRequest,
        user_id: Optional[str] = None,
    ) -> CheckoutResponse:
        now = utc_now()

        # 1. Idempotency Check: Prevent duplicate submissions
        if req.idempotency_key and req.idempotency_key.strip():
            stmt_idem = (
                select(Order)
                .where(Order.idempotency_key == req.idempotency_key.strip())
                .options(selectinload(Order.items))
            )
            res_idem = await db.execute(stmt_idem)
            existing_order = res_idem.scalar_one_or_none()
            if existing_order:
                return CheckoutService._format_order_response(existing_order)

        # 2. Get Cart
        stmt_cart = (
            select(Cart)
            .where(
                and_(
                    Cart.cart_token == req.cart_token.strip(),
                    Cart.status == CartStatus.ACTIVE.value,
                )
            )
            .options(selectinload(Cart.items).selectinload(CartItem.product))
        )
        res_cart = await db.execute(stmt_cart)
        cart = res_cart.scalar_one_or_none()
        if not cart or not cart.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Giỏ hàng của bạn đang trống hoặc phiên đặt hàng đã hết hạn.",
            )

        # 3. Validate products & calculate authoritative prices
        subtotal = 0.0
        order_items_data: List[Dict[str, Any]] = []
        calc_items: List[CartItemInput] = []

        for item in cart.items:
            prod = item.product
            if not prod:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Sản phẩm trong giỏ không còn tồn tại.",
                )

            # Invariant check: Product must be ACTIVE
            if prod.status != ProductStatus.ACTIVE.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Sản phẩm '{prod.name}' hiện không sẵn sàng để đặt hàng ({prod.status}). Vui lòng xóa khỏi giỏ để tiếp tục.",
                )

            # Calculate server authoritative price
            unit_price = float(prod.sale_price) if (prod.sale_price and prod.sale_price > 0) else float(prod.base_price)
            line_total = unit_price * item.quantity
            subtotal += line_total

            calc_items.append(
                CartItemInput(
                    product_id=prod.id,
                    category_id=prod.category_id,
                    quantity=item.quantity,
                    unit_price=unit_price,
                    name=prod.name,
                )
            )

            order_items_data.append({
                "product_id": prod.id,
                "product_name": prod.name,
                "product_sku": prod.sku,
                "product_unit": prod.unit or "phần",
                "thumbnail": prod.thumbnail,
                "unit_price": unit_price,
                "quantity": item.quantity,
                "total_price": line_total,
                "note": item.note,
            })

        # 4. Standard shipping fee
        shipping_fee = CartService.STANDARD_SHIPPING_FEE if subtotal < CartService.FREE_SHIPPING_THRESHOLD else 0.0
        discount_amount = 0.0
        shipping_discount = 0.0
        applied_promo: Optional[Promotion] = None

        # 5. Re-validate promotion again at checkout (Security guardrail)
        if cart.promo_code:
            stmt_promo = select(Promotion).where(Promotion.code == cart.promo_code)
            res_promo = await db.execute(stmt_promo)
            applied_promo = res_promo.scalar_one_or_none()
            if not applied_promo:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Mã khuyến mãi '{cart.promo_code}' không tồn tại.",
                )

            is_new_cust = True
            eff_user_id = user_id or cart.user_id
            if eff_user_id:
                res_cnt = await db.execute(select(func.count(Order.id)).where(Order.user_id == eff_user_id))
                is_new_cust = (res_cnt.scalar() or 0) == 0

            is_eligible, reason, disc, s_disc, _ = await PromotionEngine.evaluate_promotion(
                db=db,
                promo=applied_promo,
                items=calc_items,
                shipping_fee=shipping_fee,
                subtotal=subtotal,
                user_id=eff_user_id,
                is_new_customer=is_new_cust,
                as_of=now,
            )

            if not is_eligible:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Mã khuyến mãi '{cart.promo_code}' không còn hợp lệ tại thời điểm thanh toán: {reason}",
                )

            discount_amount = disc
            shipping_discount = s_disc

        final_shipping = max(0.0, shipping_fee - shipping_discount)
        final_total = max(0.0, subtotal - discount_amount + final_shipping)

        # 6. Generate human-readable order number
        date_str = now.strftime("%Y%m%d")
        rand_suffix = uuid.uuid4().hex[:4].upper()
        order_number = f"MOC-{date_str}-{rand_suffix}"

        # 7. Create Order Record
        order = Order(
            order_number=order_number,
            customer_name=req.customer_name.strip(),
            customer_phone=req.customer_phone.strip(),
            customer_email=req.customer_email.strip() if req.customer_email else None,
            delivery_address=req.delivery_address.strip(),
            customer_note=req.customer_note.strip() if req.customer_note else None,
            source=OrderSource.STOREFRONT_WEB.value,
            status=OrderStatus.NEW.value,
            payment_method=req.payment_method.value,
            payment_status=PaymentStatus.PENDING.value,
            subtotal=subtotal,
            discount_amount=discount_amount,
            shipping_fee=shipping_fee,
            shipping_discount=shipping_discount,
            total_amount=final_total,
            applied_promo_code=cart.promo_code,
            idempotency_key=req.idempotency_key.strip() if req.idempotency_key else None,
            user_id=user_id or cart.user_id,
            cart_id=cart.id,
            created_at=now,
            updated_at=now,
        )
        db.add(order)
        await db.flush()

        # 8. Create Order Items
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data["product_id"],
                product_name=item_data["product_name"],
                product_sku=item_data["product_sku"],
                product_unit=item_data["product_unit"],
                thumbnail=item_data["thumbnail"],
                unit_price=item_data["unit_price"],
                quantity=item_data["quantity"],
                total_price=item_data["total_price"],
                note=item_data["note"],
                created_at=now,
            )
            db.add(order_item)

        # 9. Create Order Status History
        history = OrderStatusHistory(
            order_id=order.id,
            previous_status=None,
            new_status=OrderStatus.NEW.value,
            changed_by_user_id=user_id,
            reason="Khách hàng đặt hàng thành công qua Website Mộc Healthy",
            created_at=now,
        )
        db.add(history)

        # 10. FEFO Stock Allocation (if active batches exist)
        for item_data in order_items_data:
            p_id = item_data["product_id"]
            qty = item_data["quantity"]
            # Check if active batches exist for this product
            stmt_b = (
                select(InventoryBatch)
                .where(
                    InventoryBatch.product_id == p_id,
                    InventoryBatch.status == BatchStatus.ACTIVE.value,
                    InventoryBatch.quantity_available > 0,
                )
                .order_by(InventoryBatch.expiry_at.asc())
            )
            res_b = await db.execute(stmt_b)
            available_batches = res_b.scalars().all()
            rem = qty
            for b in available_batches:
                if rem <= 0:
                    break
                alloc = min(b.quantity_available, rem)
                prev = b.quantity_available
                b.quantity_available = prev - alloc
                if b.quantity_available == 0:
                    b.status = BatchStatus.DEPLETED.value
                b.updated_at = now

                movement = InventoryMovement(
                    batch_id=b.id,
                    product_id=p_id,
                    movement_type=MovementType.SALE_OUT.value,
                    quantity=alloc,
                    previous_quantity=prev,
                    new_quantity=b.quantity_available,
                    reference_id=order_number,
                    reason=f"Xuất kho bán hàng đơn {order_number}",
                    created_by_user_id=user_id,
                    created_at=now,
                )
                db.add(movement)
                rem -= alloc

        # 11. Record Promotion Usage if applied
        if applied_promo:
            applied_promo.usage_count += 1
            usage = PromotionUsage(
                promotion_id=applied_promo.id,
                user_id=user_id or cart.user_id,
                order_id=order.id,
                discount_amount=discount_amount,
                created_at=now,
            )
            db.add(usage)

        # 12. Mark Cart as CONVERTED
        cart.status = CartStatus.CONVERTED.value
        cart.updated_at = now

        # 13. Auto-sync to Customer CRM
        try:
            from app.services.customer_service import CustomerService
            await CustomerService.sync_customer_from_order(db, order)
        except Exception:
            pass

        await db.commit()
        await db.refresh(order)

        # Reload order with items
        stmt_reload = (
            select(Order)
            .where(Order.id == order.id)
            .options(selectinload(Order.items))
        )
        res_reload = await db.execute(stmt_reload)
        order_loaded = res_reload.scalar_one()

        return CheckoutService._format_order_response(order_loaded)

    @staticmethod
    def _format_order_response(order: Order) -> CheckoutResponse:
        bank_instruction: Optional[BankTransferInstruction] = None
        if order.payment_method == PaymentMethod.BANK_TRANSFER.value:
            # Generate VietQR quick pay link
            transfer_content = order.order_number.replace("-", " ")
            amount_val = int(float(order.total_amount))
            qr_url = f"https://img.vietqr.io/image/MB-0901234567-compact2.png?amount={amount_val}&addInfo={transfer_content}&accountName=MOC%20HEALTHY%20FRESH%20FOOD"
            bank_instruction = BankTransferInstruction(
                bank_name="Ngân hàng TMCP Quân Đội (MBBank)",
                bank_code="MB",
                account_number="0901234567",
                account_holder="MOC HEALTHY FRESH FOOD",
                transfer_content=transfer_content,
                amount=float(order.total_amount),
                qr_code_url=qr_url,
            )

        items_snapshot = [
            OrderItemSnapshotResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product_name,
                product_sku=item.product_sku,
                product_unit=item.product_unit,
                thumbnail=item.thumbnail,
                unit_price=float(item.unit_price),
                quantity=item.quantity,
                total_price=float(item.total_price),
                note=item.note,
            )
            for item in order.items
        ]

        return CheckoutResponse(
            order_id=order.id,
            order_number=order.order_number,
            status=order.status,
            customer_name=order.customer_name,
            customer_phone=order.customer_phone,
            customer_email=order.customer_email,
            delivery_address=order.delivery_address,
            customer_note=order.customer_note,
            items=items_snapshot,
            subtotal=float(order.subtotal),
            discount_amount=float(order.discount_amount),
            shipping_fee=float(order.shipping_fee),
            shipping_discount=float(order.shipping_discount),
            total_amount=float(order.total_amount),
            payment_method=order.payment_method,
            payment_status=order.payment_status,
            applied_promo_code=order.applied_promo_code,
            bank_transfer_instruction=bank_instruction,
            created_at=order.created_at,
        )
