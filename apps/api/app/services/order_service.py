import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy import select, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

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
from app.models.auth import User
from app.models.inventory import InventoryBatch, BatchStatus, InventoryMovement, MovementType
from app.schemas.order import (
    OrderStatusUpdateRequest,
    OrderPaymentStatusUpdateRequest,
    OrderInternalNoteUpdateRequest,
    ManualOrderCreateRequest,
    AdminOrderListItemResponse,
    AdminOrderListResponse,
    AdminOrderDetailResponse,
    OrderItemResponse,
    OrderStatusHistoryResponse,
    OrderOverviewStatsResponse,
    OrderTrackingResponse,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OrderService:
    # Allowed status transition map (State Machine Guardrail)
    VALID_TRANSITIONS = {
        OrderStatus.NEW.value: [OrderStatus.CONFIRMED.value, OrderStatus.CANCELLED.value],
        OrderStatus.CONFIRMED.value: [OrderStatus.PREPARING.value, OrderStatus.CANCELLED.value],
        OrderStatus.PREPARING.value: [OrderStatus.READY.value, OrderStatus.CANCELLED.value],
        OrderStatus.READY.value: [OrderStatus.SHIPPING.value, OrderStatus.CANCELLED.value],
        OrderStatus.SHIPPING.value: [OrderStatus.COMPLETED.value, OrderStatus.CANCELLED.value],
        OrderStatus.COMPLETED.value: [OrderStatus.REFUNDED.value],
        OrderStatus.CANCELLED.value: [],
        OrderStatus.REFUNDED.value: [],
    }

    @staticmethod
    async def get_overview_stats(db: AsyncSession) -> OrderOverviewStatsResponse:
        now = utc_now()
        today_start = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=timezone.utc)

        # 1. Total orders
        res_tot = await db.execute(select(func.count(Order.id)))
        total_orders = res_tot.scalar() or 0

        # 2. New orders
        res_new = await db.execute(
            select(func.count(Order.id)).where(Order.status == OrderStatus.NEW.value)
        )
        new_orders = res_new.scalar() or 0

        # 3. In-progress orders (CONFIRMED, PREPARING, READY, SHIPPING)
        res_prog = await db.execute(
            select(func.count(Order.id)).where(
                Order.status.in_([
                    OrderStatus.CONFIRMED.value,
                    OrderStatus.PREPARING.value,
                    OrderStatus.READY.value,
                    OrderStatus.SHIPPING.value,
                ])
            )
        )
        in_progress = res_prog.scalar() or 0

        # 4. Completed today
        res_comp_today = await db.execute(
            select(func.count(Order.id)).where(
                and_(
                    Order.status == OrderStatus.COMPLETED.value,
                    Order.created_at >= today_start,
                )
            )
        )
        completed_today = res_comp_today.scalar() or 0

        # 5. Cancelled orders
        res_canc = await db.execute(
            select(func.count(Order.id)).where(Order.status == OrderStatus.CANCELLED.value)
        )
        cancelled_orders = res_canc.scalar() or 0

        # 6. Revenue today (completed orders today)
        res_rev = await db.execute(
            select(func.sum(Order.total_amount)).where(
                and_(
                    Order.status == OrderStatus.COMPLETED.value,
                    Order.created_at >= today_start,
                )
            )
        )
        revenue_today = float(res_rev.scalar() or 0.0)

        return OrderOverviewStatsResponse(
            total_orders=total_orders,
            new_orders=new_orders,
            in_progress_orders=in_progress,
            completed_today=completed_today,
            cancelled_orders=cancelled_orders,
            revenue_today=revenue_today,
        )

    @staticmethod
    async def list_orders(
        db: AsyncSession,
        search: Optional[str] = None,
        status_filter: Optional[str] = None,
        payment_status: Optional[str] = None,
        payment_method: Optional[str] = None,
        source: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> AdminOrderListResponse:
        conditions = []

        if search and search.strip():
            term = f"%{search.strip()}%"
            conditions.append(
                or_(
                    Order.order_number.ilike(term),
                    Order.customer_name.ilike(term),
                    Order.customer_phone.ilike(term),
                )
            )

        if status_filter and status_filter.strip():
            conditions.append(Order.status == status_filter.strip().upper())

        if payment_status and payment_status.strip():
            conditions.append(Order.payment_status == payment_status.strip().upper())

        if payment_method and payment_method.strip():
            conditions.append(Order.payment_method == payment_method.strip().upper())

        if source and source.strip():
            conditions.append(Order.source == source.strip().upper())

        if from_date:
            conditions.append(Order.created_at >= from_date)

        if to_date:
            conditions.append(Order.created_at <= to_date)

        base_stmt = select(Order).where(and_(*conditions)) if conditions else select(Order)

        # Count total
        count_stmt = select(func.count(Order.id)).where(and_(*conditions)) if conditions else select(func.count(Order.id))
        res_count = await db.execute(count_stmt)
        total = res_count.scalar() or 0

        # Query items with pagination
        stmt = (
            base_stmt
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        res_orders = await db.execute(stmt)
        orders = res_orders.scalars().all()

        items = [
            AdminOrderListItemResponse(
                id=o.id,
                order_number=o.order_number,
                customer_name=o.customer_name,
                customer_phone=o.customer_phone,
                delivery_address=o.delivery_address,
                source=o.source,
                status=o.status,
                payment_method=o.payment_method,
                payment_status=o.payment_status,
                total_amount=float(o.total_amount),
                items_count=sum(it.quantity for it in o.items),
                created_at=o.created_at,
            )
            for o in orders
        ]

        total_pages = max(1, (total + page_size - 1) // page_size)

        return AdminOrderListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @staticmethod
    async def get_order_detail(db: AsyncSession, order_id: str) -> AdminOrderDetailResponse:
        stmt = (
            select(Order)
            .where(or_(Order.id == order_id, Order.order_number == order_id.upper()))
            .options(
                selectinload(Order.items),
                selectinload(Order.status_history),
            )
        )
        res = await db.execute(stmt)
        order = res.scalar_one_or_none()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy đơn hàng với mã ID: {order_id}",
            )

        return OrderService._format_admin_detail(order)

    @staticmethod
    async def update_status(
        db: AsyncSession,
        order_id: str,
        req: OrderStatusUpdateRequest,
        user_id: Optional[str] = None,
    ) -> AdminOrderDetailResponse:
        stmt = (
            select(Order)
            .where(or_(Order.id == order_id, Order.order_number == order_id.upper()))
            .options(
                selectinload(Order.items),
                selectinload(Order.status_history),
            )
        )
        res = await db.execute(stmt)
        order = res.scalar_one_or_none()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy đơn hàng: {order_id}",
            )

        old_status = order.status
        new_status = req.new_status.value

        if old_status == new_status:
            return OrderService._format_admin_detail(order)

        # Validate allowed transitions
        allowed = OrderService.VALID_TRANSITIONS.get(old_status, [])
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Chuyển trạng thái không hợp lệ: từ '{old_status}' sang '{new_status}'. Các trạng thái tiếp theo hợp lệ: {allowed}",
            )

        now = utc_now()

        # Handle Cancellation: Restock inventory if previously allocated
        if new_status == OrderStatus.CANCELLED.value:
            for item in order.items:
                # Restock to active batches or create RETURN_IN movement
                stmt_batch = (
                    select(InventoryBatch)
                    .where(
                        InventoryBatch.product_id == item.product_id,
                        InventoryBatch.status == BatchStatus.ACTIVE.value,
                    )
                    .order_by(InventoryBatch.created_at.desc())
                )
                res_batch = await db.execute(stmt_batch)
                active_batch = res_batch.scalars().first()

                if active_batch:
                    prev_qty = active_batch.quantity_available
                    active_batch.quantity_available = prev_qty + item.quantity
                    active_batch.updated_at = now

                    movement = InventoryMovement(
                        batch_id=active_batch.id,
                        product_id=item.product_id,
                        movement_type=MovementType.RETURN_IN.value,
                        quantity=item.quantity,
                        previous_quantity=prev_qty,
                        new_quantity=active_batch.quantity_available,
                        reference_id=order.order_number,
                        reason=f"Hoàn kho do hủy đơn {order.order_number}: {req.reason or 'Khách hủy/Hủy bởi Admin'}",
                        created_by_user_id=user_id,
                        created_at=now,
                    )
                    db.add(movement)

        # Auto-update payment status to PAID if COMPLETED with COD
        if new_status == OrderStatus.COMPLETED.value and order.payment_method == PaymentMethod.COD.value:
            order.payment_status = PaymentStatus.PAID.value

        order.status = new_status
        order.updated_at = now

        # Add Status History
        history = OrderStatusHistory(
            order_id=order.id,
            previous_status=old_status,
            new_status=new_status,
            changed_by_user_id=user_id,
            reason=req.reason or f"Chuyển trạng thái từ {old_status} sang {new_status}",
            created_at=now,
        )
        db.add(history)

        await db.commit()
        await db.refresh(order)

        # Reload
        return await OrderService.get_order_detail(db, order.id)

    @staticmethod
    async def update_payment_status(
        db: AsyncSession,
        order_id: str,
        req: OrderPaymentStatusUpdateRequest,
        user_id: Optional[str] = None,
    ) -> AdminOrderDetailResponse:
        stmt = (
            select(Order)
            .where(or_(Order.id == order_id, Order.order_number == order_id.upper()))
            .options(
                selectinload(Order.items),
                selectinload(Order.status_history),
            )
        )
        res = await db.execute(stmt)
        order = res.scalar_one_or_none()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy đơn hàng: {order_id}",
            )

        now = utc_now()
        order.payment_status = req.payment_status.value
        order.updated_at = now

        if req.note:
            order.internal_note = (
                f"{order.internal_note}\n[{now.strftime('%d/%m/%Y %H:%M')}] Thanh toán: {req.note}"
                if order.internal_note
                else f"[{now.strftime('%d/%m/%Y %H:%M')}] Thanh toán: {req.note}"
            )

        await db.commit()
        return await OrderService.get_order_detail(db, order.id)

    @staticmethod
    async def update_internal_note(
        db: AsyncSession,
        order_id: str,
        req: OrderInternalNoteUpdateRequest,
        user_id: Optional[str] = None,
    ) -> AdminOrderDetailResponse:
        stmt = select(Order).where(or_(Order.id == order_id, Order.order_number == order_id.upper()))
        res = await db.execute(stmt)
        order = res.scalar_one_or_none()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy đơn hàng: {order_id}",
            )

        order.internal_note = req.internal_note
        order.updated_at = utc_now()
        await db.commit()
        return await OrderService.get_order_detail(db, order.id)

    @staticmethod
    async def create_manual_order(
        db: AsyncSession,
        req: ManualOrderCreateRequest,
        user_id: Optional[str] = None,
    ) -> AdminOrderDetailResponse:
        now = utc_now()

        # Validate products & calculate authoritative prices
        subtotal = 0.0
        items_to_create = []

        for it in req.items:
            res_prod = await db.execute(select(Product).where(Product.id == it.product_id))
            prod = res_prod.scalar_one_or_none()
            if not prod:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Không tìm thấy sản phẩm có mã {it.product_id}",
                )

            unit_price = float(prod.sale_price) if (prod.sale_price and prod.sale_price > 0) else float(prod.base_price)
            line_total = unit_price * it.quantity
            subtotal += line_total

            items_to_create.append({
                "product_id": prod.id,
                "product_name": prod.name,
                "product_sku": prod.sku,
                "product_unit": prod.unit or "phần",
                "thumbnail": prod.thumbnail,
                "unit_price": unit_price,
                "quantity": it.quantity,
                "total_price": line_total,
                "note": it.note,
            })

        shipping_fee = req.shipping_fee
        discount_amount = 0.0
        total_amount = max(0.0, subtotal - discount_amount + shipping_fee)

        date_str = now.strftime("%Y%m%d")
        rand_suffix = uuid.uuid4().hex[:4].upper()
        order_number = f"MOC-{date_str}-{rand_suffix}"

        order = Order(
            order_number=order_number,
            customer_name=req.customer_name.strip(),
            customer_phone=req.customer_phone.strip(),
            customer_email=req.customer_email.strip() if req.customer_email else None,
            delivery_address=req.delivery_address.strip(),
            customer_note=req.customer_note.strip() if req.customer_note else None,
            internal_note=req.internal_note.strip() if req.internal_note else None,
            source=req.source.value,
            status=OrderStatus.CONFIRMED.value,  # Manual orders created by admin default to CONFIRMED
            payment_method=req.payment_method.value,
            payment_status=req.payment_status.value,
            subtotal=subtotal,
            discount_amount=discount_amount,
            shipping_fee=shipping_fee,
            shipping_discount=0.0,
            total_amount=total_amount,
            applied_promo_code=req.applied_promo_code,
            user_id=user_id,
            created_at=now,
            updated_at=now,
        )
        db.add(order)
        await db.flush()

        for it_data in items_to_create:
            order_item = OrderItem(
                order_id=order.id,
                product_id=it_data["product_id"],
                product_name=it_data["product_name"],
                product_sku=it_data["product_sku"],
                product_unit=it_data["product_unit"],
                thumbnail=it_data["thumbnail"],
                unit_price=it_data["unit_price"],
                quantity=it_data["quantity"],
                total_price=it_data["total_price"],
                note=it_data["note"],
                created_at=now,
            )
            db.add(order_item)

        history = OrderStatusHistory(
            order_id=order.id,
            previous_status=None,
            new_status=OrderStatus.CONFIRMED.value,
            changed_by_user_id=user_id,
            reason="Nhân viên tạo đơn hàng trực tiếp tại quầy / qua điện thoại",
            created_at=now,
        )
        db.add(history)

        # Auto-sync to Customer CRM
        try:
            from app.services.customer_service import CustomerService
            await CustomerService.sync_customer_from_order(db, order)
        except Exception:
            pass

        await db.commit()
        return await OrderService.get_order_detail(db, order.id)

    @staticmethod
    async def track_order_public(
        db: AsyncSession,
        order_number: str,
        phone: Optional[str] = None,
    ) -> OrderTrackingResponse:
        stmt = (
            select(Order)
            .where(Order.order_number == order_number.strip().upper())
            .options(
                selectinload(Order.items),
                selectinload(Order.status_history),
            )
        )
        res = await db.execute(stmt)
        order = res.scalar_one_or_none()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy đơn hàng với mã '{order_number}'.",
            )

        if phone and phone.strip():
            clean_input = phone.replace(" ", "").replace(".", "").replace("-", "")
            clean_order_phone = order.customer_phone.replace(" ", "").replace(".", "").replace("-", "")
            if clean_input not in clean_order_phone and clean_order_phone not in clean_input:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Số điện thoại không khớp với thông tin người nhận của đơn hàng.",
                )

        items_resp = [
            OrderItemResponse(
                id=it.id,
                product_id=it.product_id,
                product_name=it.product_name,
                product_sku=it.product_sku,
                product_unit=it.product_unit,
                thumbnail=it.thumbnail,
                unit_price=float(it.unit_price),
                quantity=it.quantity,
                total_price=float(it.total_price),
                note=it.note,
            )
            for it in order.items
        ]

        history_resp = [
            OrderStatusHistoryResponse(
                id=h.id,
                order_id=h.order_id,
                previous_status=h.previous_status,
                new_status=h.new_status,
                changed_by_user_id=h.changed_by_user_id,
                reason=h.reason,
                created_at=h.created_at,
            )
            for h in order.status_history
        ]

        return OrderTrackingResponse(
            order_number=order.order_number,
            status=order.status,
            customer_name=order.customer_name,
            customer_phone=order.customer_phone,
            delivery_address=order.delivery_address,
            items=items_resp,
            total_amount=float(order.total_amount),
            payment_method=order.payment_method,
            payment_status=order.payment_status,
            created_at=order.created_at,
            status_history=history_resp,
        )

    @staticmethod
    def _format_admin_detail(order: Order) -> AdminOrderDetailResponse:
        items = [
            OrderItemResponse(
                id=it.id,
                product_id=it.product_id,
                product_name=it.product_name,
                product_sku=it.product_sku,
                product_unit=it.product_unit,
                thumbnail=it.thumbnail,
                unit_price=float(it.unit_price),
                quantity=it.quantity,
                total_price=float(it.total_price),
                note=it.note,
            )
            for it in order.items
        ]

        history = [
            OrderStatusHistoryResponse(
                id=h.id,
                order_id=h.order_id,
                previous_status=h.previous_status,
                new_status=h.new_status,
                changed_by_user_id=h.changed_by_user_id,
                reason=h.reason,
                created_at=h.created_at,
            )
            for h in order.status_history
        ]

        return AdminOrderDetailResponse(
            id=order.id,
            order_number=order.order_number,
            customer_name=order.customer_name,
            customer_phone=order.customer_phone,
            customer_email=order.customer_email,
            delivery_address=order.delivery_address,
            customer_note=order.customer_note,
            internal_note=order.internal_note,
            source=order.source,
            status=order.status,
            payment_method=order.payment_method,
            payment_status=order.payment_status,
            subtotal=float(order.subtotal),
            discount_amount=float(order.discount_amount),
            shipping_fee=float(order.shipping_fee),
            shipping_discount=float(order.shipping_discount),
            total_amount=float(order.total_amount),
            applied_promo_code=order.applied_promo_code,
            user_id=order.user_id,
            created_at=order.created_at,
            updated_at=order.updated_at,
            items=items,
            status_history=history,
        )
