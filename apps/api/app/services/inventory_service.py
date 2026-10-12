import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.inventory import InventoryBatch, InventoryMovement, BatchStatus, MovementType
from app.models.product import Product
from app.models.auth import User
from app.schemas.inventory import (
    BatchCreateRequest,
    BatchUpdateRequest,
    AdjustmentRequest,
    FefoAllocationRequest,
    InventoryBatchResponse,
    InventoryMovementResponse,
    ProductStockSummaryResponse,
    InventoryOverviewResponse,
    ExpiryAlertItemResponse,
    FefoAllocationResponse,
    FefoAllocationItemResponse,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def compute_batch_expiry_info(batch: InventoryBatch, now: Optional[datetime] = None) -> Dict[str, Any]:
    if now is None:
        now = utc_now()
    
    expiry = batch.expiry_at
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    diff_seconds = (expiry - now).total_seconds()
    days_to_expiry = round(diff_seconds / 86400.0, 1)
    hours_to_expiry = round(diff_seconds / 3600.0, 1)

    is_expired = diff_seconds <= 0
    is_critical = 0 < diff_seconds <= 86400  # < 24h
    is_warning = 86400 < diff_seconds <= (3 * 86400)  # <= 3 days

    return {
        "days_to_expiry": days_to_expiry,
        "hours_to_expiry": hours_to_expiry,
        "is_expired": is_expired,
        "is_critical": is_critical,
        "is_warning": is_warning,
    }


def format_batch_response(batch: InventoryBatch, now: Optional[datetime] = None) -> InventoryBatchResponse:
    expiry_info = compute_batch_expiry_info(batch, now)
    product_name = batch.product.name if batch.product else None
    product_sku = batch.product.sku if batch.product else None
    product_unit = batch.product.unit if batch.product else None

    return InventoryBatchResponse(
        id=batch.id,
        product_id=batch.product_id,
        batch_code=batch.batch_code,
        quantity_received=batch.quantity_received,
        quantity_available=batch.quantity_available,
        cost_per_unit=float(batch.cost_per_unit) if batch.cost_per_unit is not None else None,
        supplier=batch.supplier,
        received_at=batch.received_at,
        expiry_at=batch.expiry_at,
        status=batch.status,
        note=batch.note,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
        product_name=product_name,
        product_sku=product_sku,
        product_unit=product_unit,
        days_to_expiry=expiry_info["days_to_expiry"],
        hours_to_expiry=expiry_info["hours_to_expiry"],
        is_expired=expiry_info["is_expired"],
        is_critical=expiry_info["is_critical"],
        is_warning=expiry_info["is_warning"],
    )


def format_movement_response(m: InventoryMovement) -> InventoryMovementResponse:
    batch_code = m.batch.batch_code if m.batch else None
    product_name = m.product.name if m.product else None
    user_name = m.user.full_name if m.user else None

    return InventoryMovementResponse(
        id=m.id,
        batch_id=m.batch_id,
        product_id=m.product_id,
        movement_type=m.movement_type,
        quantity=m.quantity,
        previous_quantity=m.previous_quantity,
        new_quantity=m.new_quantity,
        reference_id=m.reference_id,
        reason=m.reason,
        note=m.note,
        created_by_user_id=m.created_by_user_id,
        created_at=m.created_at,
        batch_code=batch_code,
        product_name=product_name,
        created_by_user_name=user_name,
    )


class InventoryService:
    @staticmethod
    async def receive_batch(
        db: AsyncSession,
        data: BatchCreateRequest,
        user_id: Optional[str] = None,
    ) -> InventoryBatchResponse:
        # 1. Verify product exists
        res_prod = await db.execute(select(Product).where(Product.id == data.product_id))
        product = res_prod.scalar_one_or_none()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy sản phẩm với id: {data.product_id}",
            )

        # 2. Generate batch code if not provided
        now = utc_now()
        batch_code = data.batch_code
        if not batch_code or not batch_code.strip():
            date_part = now.strftime("%Y%m%d")
            rand_part = uuid.uuid4().hex[:6].upper()
            batch_code = f"BATCH-{date_part}-{rand_part}"
        else:
            batch_code = batch_code.strip()

        # Check unique batch code
        res_code = await db.execute(
            select(InventoryBatch).where(InventoryBatch.batch_code == batch_code)
        )
        if res_code.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Mã lô hàng '{batch_code}' đã tồn tại trong hệ thống.",
            )

        received_at = data.received_at or now

        # 3. Create batch
        batch = InventoryBatch(
            product_id=product.id,
            batch_code=batch_code,
            quantity_received=data.quantity_received,
            quantity_available=data.quantity_received,
            cost_per_unit=data.cost_per_unit if data.cost_per_unit is not None else product.cost_price,
            supplier=data.supplier,
            received_at=received_at,
            expiry_at=data.expiry_at,
            status=BatchStatus.ACTIVE.value,
            note=data.note,
            created_at=now,
            updated_at=now,
        )
        db.add(batch)
        await db.flush()

        # 4. Create movement record (Never update stock directly without movement)
        movement = InventoryMovement(
            batch_id=batch.id,
            product_id=product.id,
            movement_type=MovementType.PURCHASE_IN.value,
            quantity=data.quantity_received,
            previous_quantity=0,
            new_quantity=data.quantity_received,
            reason=f"Nhập kho theo lô ({batch_code})",
            note=data.note,
            created_by_user_id=user_id,
            created_at=now,
        )
        db.add(movement)
        await db.commit()
        await db.refresh(batch)

        # Eager load product relationship for formatting
        res_reload = await db.execute(
            select(InventoryBatch).where(InventoryBatch.id == batch.id)
        )
        batch = res_reload.scalar_one()
        return format_batch_response(batch, now)

    @staticmethod
    async def adjust_stock(
        db: AsyncSession,
        data: AdjustmentRequest,
        user_id: Optional[str] = None,
    ) -> InventoryMovementResponse:
        res_batch = await db.execute(
            select(InventoryBatch).where(InventoryBatch.id == data.batch_id)
        )
        batch = res_batch.scalar_one_or_none()
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy lô hàng với id: {data.batch_id}",
            )

        now = utc_now()
        qty = data.quantity
        prev_qty = batch.quantity_available

        if data.movement_type in [MovementType.ADJUSTMENT_IN, MovementType.RETURN_IN]:
            new_qty = prev_qty + qty
            batch.quantity_available = new_qty
            if batch.status == BatchStatus.DEPLETED.value and new_qty > 0:
                batch.status = BatchStatus.ACTIVE.value
        elif data.movement_type in [MovementType.ADJUSTMENT_OUT, MovementType.WASTE_OUT]:
            # Guardrail: Negative stock protection
            if prev_qty < qty:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Số lượng yêu cầu ({qty}) vượt quá số lượng tồn kho khả dụng ({prev_qty}) của lô {batch.batch_code}.",
                )
            new_qty = prev_qty - qty
            batch.quantity_available = new_qty
            if new_qty == 0:
                if data.movement_type == MovementType.WASTE_OUT:
                    batch.status = BatchStatus.DISCARDED.value
                else:
                    batch.status = BatchStatus.DEPLETED.value
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Loại điều chỉnh '{data.movement_type}' không được hỗ trợ trong endpoint này.",
            )

        batch.updated_at = now

        # Create movement ledger record
        movement = InventoryMovement(
            batch_id=batch.id,
            product_id=batch.product_id,
            movement_type=data.movement_type.value,
            quantity=qty,
            previous_quantity=prev_qty,
            new_quantity=new_qty,
            reference_id=data.reference_id,
            reason=data.reason,
            note=data.note,
            created_by_user_id=user_id,
            created_at=now,
        )
        db.add(movement)
        await db.commit()
        await db.refresh(movement)

        # Reload for relation names
        res_reload = await db.execute(
            select(InventoryMovement).where(InventoryMovement.id == movement.id)
        )
        movement = res_reload.scalar_one()
        return format_movement_response(movement)

    @staticmethod
    async def fefo_allocate(
        db: AsyncSession,
        data: FefoAllocationRequest,
        user_id: Optional[str] = None,
        dry_run: bool = False,
    ) -> FefoAllocationResponse:
        # 1. Verify product
        res_prod = await db.execute(select(Product).where(Product.id == data.product_id))
        product = res_prod.scalar_one_or_none()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy sản phẩm với id: {data.product_id}",
            )

        now = utc_now()

        # 2. Query active batches ordered by FEFO (expiry_at ASC, created_at ASC)
        stmt = (
            select(InventoryBatch)
            .where(
                InventoryBatch.product_id == data.product_id,
                InventoryBatch.status == BatchStatus.ACTIVE.value,
                InventoryBatch.quantity_available > 0,
            )
            .order_by(asc(InventoryBatch.expiry_at), asc(InventoryBatch.created_at))
        )
        res_batches = await db.execute(stmt)
        batches = list(res_batches.scalars().all())

        total_available = sum(b.quantity_available for b in batches)
        if total_available < data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không đủ tồn kho khả dụng để xuất theo FEFO. Yêu cầu {data.quantity}, hiện có {total_available}.",
            )

        remaining = data.quantity
        allocations: List[FefoAllocationItemResponse] = []

        for b in batches:
            if remaining <= 0:
                break
            alloc_qty = min(b.quantity_available, remaining)
            qty_before = b.quantity_available
            qty_after = qty_before - alloc_qty

            allocations.append(
                FefoAllocationItemResponse(
                    batch_id=b.id,
                    batch_code=b.batch_code,
                    allocated_quantity=alloc_qty,
                    quantity_before=qty_before,
                    quantity_after=qty_after,
                    expiry_at=b.expiry_at,
                )
            )

            if not dry_run:
                b.quantity_available = qty_after
                if qty_after == 0:
                    b.status = BatchStatus.DEPLETED.value
                b.updated_at = now

                movement = InventoryMovement(
                    batch_id=b.id,
                    product_id=b.product_id,
                    movement_type=MovementType.SALE_OUT.value,
                    quantity=alloc_qty,
                    previous_quantity=qty_before,
                    new_quantity=qty_after,
                    reference_id=data.reference_id,
                    reason=f"Xuất kho FEFO theo tham chiếu {data.reference_id or 'Đơn hàng'}",
                    note=data.note,
                    created_by_user_id=user_id,
                    created_at=now,
                )
                db.add(movement)

            remaining -= alloc_qty

        if not dry_run:
            await db.commit()

        total_allocated = sum(item.allocated_quantity for item in allocations)
        return FefoAllocationResponse(
            product_id=product.id,
            product_name=product.name,
            requested_quantity=data.quantity,
            allocated_quantity=total_allocated,
            is_fully_allocated=(total_allocated == data.quantity),
            allocations=allocations,
        )

    @staticmethod
    async def get_overview(db: AsyncSession) -> InventoryOverviewResponse:
        now = utc_now()
        three_days_later = now + timedelta(days=3)
        one_day_later = now + timedelta(days=1)

        # Total products count
        res_prod_count = await db.execute(select(func.count(Product.id)))
        total_products = res_prod_count.scalar() or 0

        # Batches
        res_batches = await db.execute(select(InventoryBatch))
        all_batches = list(res_batches.scalars().all())

        total_batches = len(all_batches)
        total_stock_units = 0
        total_inventory_value = 0.0
        expiring_soon_count = 0
        critical_count = 0
        expired_count = 0

        product_stock_map: Dict[str, int] = {}

        for b in all_batches:
            if b.status == BatchStatus.ACTIVE.value and b.quantity_available > 0:
                total_stock_units += b.quantity_available
                unit_cost = float(b.cost_per_unit) if b.cost_per_unit is not None else 0.0
                total_inventory_value += b.quantity_available * unit_cost

                product_stock_map[b.product_id] = (
                    product_stock_map.get(b.product_id, 0) + b.quantity_available
                )

                expiry = b.expiry_at
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)

                if expiry <= now:
                    expired_count += 1
                elif expiry <= one_day_later:
                    critical_count += 1
                    expiring_soon_count += 1
                elif expiry <= three_days_later:
                    expiring_soon_count += 1

        # Calculate low stock products
        res_all_products = await db.execute(select(Product))
        products = list(res_all_products.scalars().all())
        low_stock_products_count = 0

        for p in products:
            curr_stock = product_stock_map.get(p.id, 0)
            if curr_stock <= p.low_stock_threshold:
                low_stock_products_count += 1

        return InventoryOverviewResponse(
            total_products=total_products,
            total_batches=total_batches,
            total_stock_units=total_stock_units,
            low_stock_products_count=low_stock_products_count,
            expiring_soon_batches_count=expiring_soon_count,
            critical_batches_count=critical_count,
            expired_batches_count=expired_count,
            total_inventory_value=round(total_inventory_value, 2),
        )

    @staticmethod
    async def get_product_stock_summaries(
        db: AsyncSession,
        search: Optional[str] = None,
        low_stock_only: bool = False,
        expiring_soon_only: bool = False,
    ) -> List[ProductStockSummaryResponse]:
        now = utc_now()
        three_days_later = now + timedelta(days=3)

        stmt = select(Product).order_by(Product.name)
        if search and search.strip():
            s = f"%{search.strip()}%"
            stmt = stmt.where(or_(Product.name.ilike(s), Product.sku.ilike(s)))

        res_prods = await db.execute(stmt)
        products = list(res_prods.scalars().all())

        results: List[ProductStockSummaryResponse] = []

        for p in products:
            active_batches = [
                b for b in p.batches
                if b.status == BatchStatus.ACTIVE.value and b.quantity_available > 0
            ]
            total_available = sum(b.quantity_available for b in active_batches)
            batch_count = len(active_batches)

            nearest_expiry: Optional[datetime] = None
            has_expiring = False
            has_expired = False

            if active_batches:
                sorted_by_expiry = sorted(active_batches, key=lambda x: x.expiry_at)
                nearest_expiry = sorted_by_expiry[0].expiry_at

                for b in active_batches:
                    exp = b.expiry_at
                    if exp.tzinfo is None:
                        exp = exp.replace(tzinfo=timezone.utc)
                    if exp <= now:
                        has_expired = True
                    elif exp <= three_days_later:
                        has_expiring = True

            is_low = total_available <= p.low_stock_threshold

            if low_stock_only and not is_low:
                continue
            if expiring_soon_only and not (has_expiring or has_expired):
                continue

            results.append(
                ProductStockSummaryResponse(
                    product_id=p.id,
                    product_name=p.name,
                    sku=p.sku,
                    unit=p.unit,
                    base_price=float(p.base_price),
                    sale_price=float(p.sale_price) if p.sale_price is not None else None,
                    cost_price=float(p.cost_price) if p.cost_price is not None else None,
                    low_stock_threshold=p.low_stock_threshold,
                    total_available=total_available,
                    batch_count=batch_count,
                    nearest_expiry=nearest_expiry,
                    is_low_stock=is_low,
                    has_expiring_batches=has_expiring,
                    has_expired_batches=has_expired,
                )
            )

        return results

    @staticmethod
    async def get_expiry_alerts(db: AsyncSession) -> List[ExpiryAlertItemResponse]:
        now = utc_now()
        stmt = (
            select(InventoryBatch)
            .where(
                InventoryBatch.status == BatchStatus.ACTIVE.value,
                InventoryBatch.quantity_available > 0,
            )
            .order_by(asc(InventoryBatch.expiry_at))
        )
        res_batches = await db.execute(stmt)
        batches = list(res_batches.scalars().all())

        alerts: List[ExpiryAlertItemResponse] = []

        for b in batches:
            exp = b.expiry_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)

            diff_sec = (exp - now).total_seconds()
            days = round(diff_sec / 86400.0, 1)
            hours = round(diff_sec / 3600.0, 1)

            if diff_sec <= 0:
                urgency = "EXPIRED"
            elif diff_sec <= 86400:  # < 24h
                urgency = "CRITICAL"
            elif diff_sec <= (3 * 86400):  # <= 3 days
                urgency = "WARNING"
            elif diff_sec <= (7 * 86400):  # <= 7 days
                urgency = "ATTENTION"
            else:
                continue  # Hạn dùng xa (> 7 ngày), không thuộc diện cảnh báo nguy cơ

            unit_cost = (
                float(b.cost_per_unit)
                if b.cost_per_unit is not None
                else (float(b.product.cost_price) if b.product and b.product.cost_price else 0.0)
            )
            waste_cost = round(b.quantity_available * unit_cost, 2)

            alerts.append(
                ExpiryAlertItemResponse(
                    batch_id=b.id,
                    product_id=b.product_id,
                    product_name=b.product.name if b.product else "",
                    product_sku=b.product.sku if b.product else "",
                    batch_code=b.batch_code,
                    quantity_available=b.quantity_available,
                    expiry_at=b.expiry_at,
                    days_to_expiry=days,
                    hours_to_expiry=hours,
                    urgency=urgency,
                    estimated_waste_cost=waste_cost,
                )
            )

        # Sort priority: EXPIRED first, CRITICAL second, WARNING third, ATTENTION fourth
        priority_map = {"EXPIRED": 0, "CRITICAL": 1, "WARNING": 2, "ATTENTION": 3}
        alerts.sort(key=lambda a: (priority_map.get(a.urgency, 99), a.hours_to_expiry))
        return alerts
