import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from fastapi import HTTPException

from app.models.omnichannel import (
    MarketplaceImport,
    Settlement,
    SettlementOrder,
    MarketplaceChannel,
    ImportStatus,
    ReconciliationStatus,
)
from app.models.order import Order, OrderItem, OrderStatusHistory, OrderStatus, PaymentStatus, PaymentMethod
from app.models.product import Product
from app.services.omnichannel.provider import get_order_provider, NormalizedOrderRow
from app.schemas.omnichannel import (
    MarketplaceImportPreviewItem,
    MarketplaceImportPreviewResponse,
    MarketplaceImportResponse,
    SettlementCreateRequest,
    SettlementResponse,
    SettlementDetailResponse,
    SettlementOrderResponse,
    SettlementReconcileResult,
    ChannelPnLSummary,
    OmnichannelPnLResponse,
)


class OmnichannelService:
    @staticmethod
    async def preview_import(
        session: AsyncSession,
        channel: str,
        filename: str,
        content: str,
    ) -> MarketplaceImportPreviewResponse:
        provider = get_order_provider(channel)
        rows: List[NormalizedOrderRow] = provider.parse_file_content(content, filename)

        if not rows:
            return MarketplaceImportPreviewResponse(
                channel=channel,
                filename=filename,
                total_rows=0,
                valid_rows=0,
                duplicate_rows=0,
                error_rows=0,
                gross_amount_total=0.0,
                platform_fee_total=0.0,
                merchant_discount_total=0.0,
                net_settlement_total=0.0,
                preview_items=[],
            )

        # Detect duplicates in DB
        ext_ids = [r.external_order_id for r in rows if r.external_order_id]
        existing_ids = set()
        if ext_ids:
            query = select(Order.external_order_id).where(
                and_(
                    Order.channel == channel.upper(),
                    Order.external_order_id.in_(ext_ids),
                )
            )
            res = await session.execute(query)
            existing_ids = {row[0] for row in res.fetchall() if row[0]}

        seen_in_file = set()
        preview_items: List[MarketplaceImportPreviewItem] = []
        valid_count = 0
        duplicate_count = 0
        error_count = 0
        gross_sum = 0.0
        fee_sum = 0.0
        discount_sum = 0.0
        net_sum = 0.0

        for idx, r in enumerate(rows, start=1):
            is_dup = r.external_order_id in existing_ids or r.external_order_id in seen_in_file
            if is_dup:
                duplicate_count += 1
            else:
                valid_count += 1
                seen_in_file.add(r.external_order_id)

            if r.error:
                error_count += 1

            gross_sum += r.gross_amount
            fee_sum += r.platform_fee
            discount_sum += r.merchant_discount
            net_sum += r.net_amount

            preview_items.append(
                MarketplaceImportPreviewItem(
                    row_index=idx,
                    external_order_id=r.external_order_id,
                    channel=r.channel,
                    customer_name=r.customer_name,
                    customer_phone=r.customer_phone,
                    ordered_at=r.ordered_at.strftime("%Y-%m-%d %H:%M"),
                    gross_amount=r.gross_amount,
                    merchant_discount=r.merchant_discount,
                    platform_fee=r.platform_fee,
                    net_amount=r.net_amount,
                    items_count=len(r.items),
                    is_duplicate=is_dup,
                    error=r.error,
                )
            )

        return MarketplaceImportPreviewResponse(
            channel=channel.upper(),
            filename=filename,
            total_rows=len(rows),
            valid_rows=valid_count,
            duplicate_rows=duplicate_count,
            error_rows=error_count,
            gross_amount_total=gross_sum,
            platform_fee_total=fee_sum,
            merchant_discount_total=discount_sum,
            net_settlement_total=net_sum,
            preview_items=preview_items,
        )

    @staticmethod
    async def execute_import(
        session: AsyncSession,
        user_id: Optional[str],
        channel: str,
        filename: str,
        content: str,
        skip_duplicates: bool = True,
    ) -> MarketplaceImportResponse:
        channel_upper = channel.strip().upper()
        provider = get_order_provider(channel_upper)
        rows: List[NormalizedOrderRow] = provider.parse_file_content(content, filename)

        if not rows:
            raise HTTPException(status_code=400, detail="Tập tin không chứa dữ liệu đơn hàng hợp lệ để nhập.")

        # Default fallback product for line items
        res_p = await session.execute(select(Product).limit(1))
        fallback_product = res_p.scalar_one_or_none()

        import_rec = MarketplaceImport(
            channel=channel_upper,
            filename=filename,
            file_format="CSV",
            status=ImportStatus.PROCESSING.value,
            total_rows=len(rows),
            created_by_user_id=user_id,
            started_at=datetime.now(timezone.utc),
        )
        session.add(import_rec)
        await session.flush()

        # Query existing external IDs
        ext_ids = [r.external_order_id for r in rows if r.external_order_id]
        existing_ids = set()
        if ext_ids:
            query = select(Order.external_order_id).where(
                and_(
                    Order.channel == channel_upper,
                    Order.external_order_id.in_(ext_ids),
                )
            )
            res = await session.execute(query)
            existing_ids = {row[0] for row in res.fetchall() if row[0]}

        imported_count = 0
        duplicate_count = 0
        rejected_count = 0
        gross_total = 0.0
        fee_total = 0.0
        discount_total = 0.0
        net_total = 0.0
        seen_in_batch = set()

        for idx, r in enumerate(rows, start=1):
            if r.external_order_id in existing_ids or r.external_order_id in seen_in_batch:
                duplicate_count += 1
                if skip_duplicates:
                    continue
            seen_in_batch.add(r.external_order_id)

            # Generate unique internal order number
            rnd = uuid.uuid4().hex[:6].upper()
            date_prefix = r.ordered_at.strftime("%y%m%d")
            chan_tag = channel_upper[:3]
            order_number = f"MOC-{chan_tag}-{date_prefix}-{rnd}"

            order = Order(
                order_number=order_number,
                customer_name=r.customer_name,
                customer_phone=r.customer_phone,
                delivery_address=r.delivery_address,
                customer_note=r.customer_note,
                internal_note=f"Nhập tự động từ báo cáo {channel_upper} (Mã đối tác: {r.external_order_id})",
                source=channel_upper,
                channel=channel_upper,
                external_order_id=r.external_order_id,
                status=OrderStatus.COMPLETED.value,
                payment_method=PaymentMethod.BANK_TRANSFER.value,
                payment_status=PaymentStatus.PAID.value,
                subtotal=r.gross_amount,
                gross_amount=r.gross_amount,
                discount_amount=r.merchant_discount,
                merchant_discount=r.merchant_discount,
                platform_fee=r.platform_fee,
                other_fee=r.other_fee,
                net_amount=r.net_amount,
                total_amount=r.gross_amount,
                shipping_fee=0.0,
                shipping_discount=0.0,
                raw_import_id=import_rec.id,
                created_at=r.ordered_at,
                updated_at=r.ordered_at,
            )
            session.add(order)
            await session.flush()

            # Add items
            for it in r.items:
                prod_id = fallback_product.id if fallback_product else str(uuid.uuid4())
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=prod_id,
                    product_name=it.product_name,
                    product_sku=it.product_sku,
                    product_unit=it.product_unit,
                    unit_price=it.unit_price,
                    quantity=it.quantity,
                    total_price=it.total_price,
                    note=it.note,
                    created_at=r.ordered_at,
                )
                session.add(order_item)

            # Add status audit history
            session.add(
                OrderStatusHistory(
                    order_id=order.id,
                    previous_status=None,
                    new_status=OrderStatus.COMPLETED.value,
                    changed_by_user_id=user_id,
                    reason=f"Nhập hoàn tất từ file {filename} ({channel_upper})",
                    created_at=r.ordered_at,
                )
            )

            imported_count += 1
            gross_total += r.gross_amount
            fee_total += r.platform_fee
            discount_total += r.merchant_discount
            net_total += r.net_amount

        # Update import record
        import_rec.status = ImportStatus.COMPLETED.value
        import_rec.imported_rows = imported_count
        import_rec.duplicate_rows = duplicate_count
        import_rec.rejected_rows = rejected_count
        import_rec.gross_amount_total = gross_total
        import_rec.platform_fee_total = fee_total
        import_rec.merchant_discount_total = discount_total
        import_rec.net_settlement_total = net_total
        import_rec.completed_at = datetime.now(timezone.utc)

        await session.commit()
        await session.refresh(import_rec)

        return MarketplaceImportResponse(
            id=import_rec.id,
            channel=import_rec.channel,
            filename=import_rec.filename,
            file_format=import_rec.file_format,
            status=import_rec.status,
            total_rows=import_rec.total_rows,
            imported_rows=import_rec.imported_rows,
            duplicate_rows=import_rec.duplicate_rows,
            rejected_rows=import_rec.rejected_rows,
            gross_amount_total=float(import_rec.gross_amount_total),
            platform_fee_total=float(import_rec.platform_fee_total),
            merchant_discount_total=float(import_rec.merchant_discount_total),
            net_settlement_total=float(import_rec.net_settlement_total),
            started_at=import_rec.started_at.isoformat(),
            completed_at=import_rec.completed_at.isoformat() if import_rec.completed_at else None,
        )

    @staticmethod
    async def list_imports(
        session: AsyncSession,
        channel: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> List[MarketplaceImportResponse]:
        query = select(MarketplaceImport).order_by(desc(MarketplaceImport.started_at))
        if channel:
            query = query.where(MarketplaceImport.channel == channel.upper())

        query = query.offset((page - 1) * page_size).limit(page_size)
        res = await session.execute(query)
        items = res.scalars().all()

        return [
            MarketplaceImportResponse(
                id=it.id,
                channel=it.channel,
                filename=it.filename,
                file_format=it.file_format,
                status=it.status,
                total_rows=it.total_rows,
                imported_rows=it.imported_rows,
                duplicate_rows=it.duplicate_rows,
                rejected_rows=it.rejected_rows,
                gross_amount_total=float(it.gross_amount_total),
                platform_fee_total=float(it.platform_fee_total),
                merchant_discount_total=float(it.merchant_discount_total),
                net_settlement_total=float(it.net_settlement_total),
                started_at=it.started_at.isoformat(),
                completed_at=it.completed_at.isoformat() if it.completed_at else None,
            )
            for it in items
        ]

    @staticmethod
    async def create_settlement(
        session: AsyncSession,
        data: SettlementCreateRequest,
    ) -> SettlementResponse:
        net = max(0.0, data.gross_amount - data.platform_fee - data.merchant_discount - data.other_fee)
        settlement = Settlement(
            channel=data.channel.upper(),
            external_settlement_id=data.external_settlement_id,
            period_start=data.period_start,
            period_end=data.period_end,
            gross_amount=data.gross_amount,
            platform_fee=data.platform_fee,
            merchant_discount=data.merchant_discount,
            other_fee=data.other_fee,
            net_amount=net,
            status=ReconciliationStatus.UNMATCHED.value,
            notes=data.notes,
        )
        session.add(settlement)
        await session.commit()
        await session.refresh(settlement)

        return SettlementResponse(
            id=settlement.id,
            channel=settlement.channel,
            external_settlement_id=settlement.external_settlement_id,
            period_start=settlement.period_start.isoformat(),
            period_end=settlement.period_end.isoformat(),
            gross_amount=float(settlement.gross_amount),
            platform_fee=float(settlement.platform_fee),
            merchant_discount=float(settlement.merchant_discount),
            other_fee=float(settlement.other_fee),
            net_amount=float(settlement.net_amount),
            status=settlement.status,
            paid_at=settlement.paid_at.isoformat() if settlement.paid_at else None,
            notes=settlement.notes,
            matched_orders_count=0,
            matched_amount=0.0,
            discrepancy_amount=float(settlement.net_amount),
            created_at=settlement.created_at.isoformat(),
        )

    @staticmethod
    async def list_settlements(
        session: AsyncSession,
        channel: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[SettlementResponse]:
        query = select(Settlement).order_by(desc(Settlement.period_start))
        if channel:
            query = query.where(Settlement.channel == channel.upper())
        if status:
            query = query.where(Settlement.status == status.upper())

        res = await session.execute(query)
        items = res.scalars().all()

        results = []
        for s in items:
            matched_orders = s.settlement_orders
            matched_sum = sum(float(so.allocated_amount) for so in matched_orders)
            net_val = float(s.net_amount)
            results.append(
                SettlementResponse(
                    id=s.id,
                    channel=s.channel,
                    external_settlement_id=s.external_settlement_id,
                    period_start=s.period_start.isoformat(),
                    period_end=s.period_end.isoformat(),
                    gross_amount=float(s.gross_amount),
                    platform_fee=float(s.platform_fee),
                    merchant_discount=float(s.merchant_discount),
                    other_fee=float(s.other_fee),
                    net_amount=net_val,
                    status=s.status,
                    paid_at=s.paid_at.isoformat() if s.paid_at else None,
                    notes=s.notes,
                    matched_orders_count=len(matched_orders),
                    matched_amount=matched_sum,
                    discrepancy_amount=abs(net_val - matched_sum),
                    created_at=s.created_at.isoformat(),
                )
            )
        return results

    @staticmethod
    async def reconcile_settlement(
        session: AsyncSession,
        settlement_id: str,
    ) -> SettlementReconcileResult:
        res = await session.execute(select(Settlement).where(Settlement.id == settlement_id))
        settlement = res.scalar_one_or_none()
        if not settlement:
            raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi quyết toán")

        # Query all orders in the channel within [period_start, period_end]
        query = select(Order).where(
            and_(
                Order.channel == settlement.channel,
                Order.created_at >= settlement.period_start,
                Order.created_at <= settlement.period_end,
            )
        )
        res_orders = await session.execute(query)
        period_orders = res_orders.scalars().all()

        # Clear old matched records for this settlement
        await session.execute(
            SettlementOrder.__table__.delete().where(SettlementOrder.settlement_id == settlement_id)
        )

        matched_count = 0
        total_orders_net = 0.0

        for ord in period_orders:
            allocated = float(ord.net_amount or ord.total_amount)
            total_orders_net += allocated
            matched_count += 1

            so = SettlementOrder(
                settlement_id=settlement.id,
                order_id=ord.id,
                allocated_amount=allocated,
                platform_fee=float(ord.platform_fee or 0.0),
                merchant_discount=float(ord.merchant_discount or 0.0),
                status="MATCHED",
                matched_at=datetime.now(timezone.utc),
            )
            session.add(so)

            # Mark order as settled
            ord.settled_at = datetime.now(timezone.utc)

        settlement_net = float(settlement.net_amount)
        discrepancy = abs(settlement_net - total_orders_net)

        if matched_count == 0:
            settlement.status = ReconciliationStatus.UNMATCHED.value
        elif discrepancy <= 1000.0:  # tolerance under 1000 VND for rounding
            settlement.status = ReconciliationStatus.MATCHED.value
        else:
            settlement.status = ReconciliationStatus.PARTIAL.value

        await session.commit()
        await session.refresh(settlement)

        return SettlementReconcileResult(
            settlement_id=settlement.id,
            status=settlement.status,
            total_orders_in_period=len(period_orders),
            matched_orders=matched_count,
            unmatched_orders=0,
            total_settlement_net=settlement_net,
            total_orders_net=total_orders_net,
            discrepancy=discrepancy,
        )

    @staticmethod
    async def get_channel_pnl(
        session: AsyncSession,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> OmnichannelPnLResponse:
        """
        Calculates omnichannel P&L breakdown by channel (Website vs GrabFood vs ShopeeFood vs POS).
        Gross Revenue -> Platform Fees -> Merchant Discounts -> Net Settlement.
        """
        filters = []
        if period_start:
            filters.append(Order.created_at >= period_start)
        if period_end:
            filters.append(Order.created_at <= period_end)

        query = select(Order)
        if filters:
            query = query.where(and_(*filters))

        res = await session.execute(query)
        orders = res.scalars().all()

        channels_data: Dict[str, Dict[str, float]] = {}

        for o in orders:
            ch = (o.channel or o.source or "WEBSITE").upper()
            if ch not in channels_data:
                channels_data[ch] = {
                    "count": 0,
                    "gross": 0.0,
                    "discount": 0.0,
                    "fees": 0.0,
                    "net": 0.0,
                }

            gross = float(o.gross_amount or o.total_amount)
            discount = float(o.merchant_discount or o.discount_amount or 0.0)
            fee = float(o.platform_fee or 0.0)
            net = float(o.net_amount if o.net_amount is not None else (gross - discount - fee))

            channels_data[ch]["count"] += 1
            channels_data[ch]["gross"] += gross
            channels_data[ch]["discount"] += discount
            channels_data[ch]["fees"] += fee
            channels_data[ch]["net"] += net

        channel_summaries: List[ChannelPnLSummary] = []
        tot_count = 0
        tot_gross = 0.0
        tot_disc = 0.0
        tot_fees = 0.0
        tot_net = 0.0

        for ch, d in sorted(channels_data.items(), key=lambda x: x[1]["gross"], reverse=True):
            cnt = int(d["count"])
            g = d["gross"]
            net = d["net"]
            aov = round(g / max(1, cnt), 0)
            net_order = round(net / max(1, cnt), 0)
            margin = round((net / g * 100), 1) if g > 0 else 0.0

            channel_summaries.append(
                ChannelPnLSummary(
                    channel=ch,
                    order_count=cnt,
                    gross_revenue=g,
                    merchant_discount=d["discount"],
                    platform_fees=d["fees"],
                    net_settlement=net,
                    average_order_value=aov,
                    net_revenue_per_order=net_order,
                    net_margin_percentage=margin,
                )
            )

            tot_count += cnt
            tot_gross += g
            tot_disc += d["discount"]
            tot_fees += d["fees"]
            tot_net += net

        tot_aov = round(tot_gross / max(1, tot_count), 0)
        tot_net_order = round(tot_net / max(1, tot_count), 0)
        tot_margin = round((tot_net / tot_gross * 100), 1) if tot_gross > 0 else 0.0

        totals_summary = ChannelPnLSummary(
            channel="TOTAL",
            order_count=tot_count,
            gross_revenue=tot_gross,
            merchant_discount=tot_disc,
            platform_fees=tot_fees,
            net_settlement=tot_net,
            average_order_value=tot_aov,
            net_revenue_per_order=tot_net_order,
            net_margin_percentage=tot_margin,
        )

        return OmnichannelPnLResponse(
            period_start=period_start.isoformat() if period_start else None,
            period_end=period_end.isoformat() if period_end else None,
            channels=channel_summaries,
            totals=totals_summary,
        )
