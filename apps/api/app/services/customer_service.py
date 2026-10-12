from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, func, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.customer import (
    Customer,
    CustomerAddress,
    LoyaltyTransaction,
    CustomerSegment,
    LoyaltyTransactionType,
)
from app.models.order import Order, OrderItem
from app.schemas.customer import (
    CustomerCreateInput,
    CustomerUpdateInput,
    Customer360Response,
    CustomerOrderSummary,
    FavoriteProductItem,
    LoyaltyTransactionResponse,
    CustomerOverviewStats,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def calculate_rfm_segment(
    order_count: int,
    total_spent: float,
    last_order_at: Optional[datetime],
    aov: float,
) -> str:
    """
    Rule-based RFM algorithm for F&B customer classification:
    - NEW: 0 or 1 order placed recently (< 14 days)
    - REPEAT: 2 to 7 orders, returning customer
    - VIP: >= 8 orders OR total_spent >= 2,000,000 VND
    - AT_RISK: last order was 30-60 days ago
    - DORMANT: last order > 60 days ago
    - HIGH_VALUE: AOV >= 250,000 VND
    """
    if order_count == 0:
        return CustomerSegment.NEW.value

    now = utc_now()
    days_since_last_order = 0
    if last_order_at:
        # Normalize timezone
        if last_order_at.tzinfo is None:
            last_order_dt = last_order_at.replace(tzinfo=timezone.utc)
        else:
            last_order_dt = last_order_at
        days_since_last_order = (now - last_order_dt).days

    # Inactivity check
    if days_since_last_order > 60 and order_count > 0:
        return CustomerSegment.DORMANT.value

    if days_since_last_order > 30 and order_count > 0:
        return CustomerSegment.AT_RISK.value

    # VIP check
    if total_spent >= 2000000 or order_count >= 8:
        return CustomerSegment.VIP.value

    # High Value check
    if aov >= 250000 and order_count >= 2:
        return CustomerSegment.HIGH_VALUE.value

    # Repeat vs New
    if order_count >= 2:
        return CustomerSegment.REPEAT.value

    return CustomerSegment.ACTIVE.value if days_since_last_order <= 14 else CustomerSegment.NEW.value


class CustomerService:
    @staticmethod
    async def get_by_id(db: AsyncSession, customer_id: str) -> Customer:
        res = await db.execute(select(Customer).where(Customer.id == customer_id))
        cust = res.scalar_one_or_none()
        if not cust:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy khách hàng với mã {customer_id}",
            )
        return cust

    @staticmethod
    async def get_by_phone(db: AsyncSession, phone: str) -> Optional[Customer]:
        clean_phone = phone.strip().replace(" ", "").replace(".", "")
        res = await db.execute(select(Customer).where(Customer.phone == clean_phone))
        return res.scalar_one_or_none()

    @staticmethod
    async def get_or_create_by_phone(
        db: AsyncSession,
        phone: str,
        full_name: str = "Khách hàng",
        email: Optional[str] = None,
        address: Optional[str] = None,
        source: str = "ONLINE",
    ) -> Customer:
        clean_phone = phone.strip().replace(" ", "").replace(".", "")
        cust = await CustomerService.get_by_phone(db, clean_phone)
        if not cust:
            cust = Customer(
                phone=clean_phone,
                full_name=full_name.strip() if full_name else "Khách hàng",
                email=email.strip() if email else None,
                default_address=address.strip() if address else None,
                source=source,
                segment=CustomerSegment.NEW.value,
                order_count=0,
                total_spent=0.0,
                average_order_value=0.0,
                loyalty_points=0,
                tags=[],
            )
            db.add(cust)
            await db.flush()
        else:
            # Enrich existing info if missing
            if not cust.email and email:
                cust.email = email.strip()
            if not cust.default_address and address:
                cust.default_address = address.strip()
            if cust.full_name in ("Khách hàng", "Khách vãng lai") and full_name:
                cust.full_name = full_name.strip()
        return cust

    @staticmethod
    async def create_customer(
        db: AsyncSession,
        data: CustomerCreateInput,
    ) -> Customer:
        clean_phone = data.phone.strip().replace(" ", "").replace(".", "")
        existing = await CustomerService.get_by_phone(db, clean_phone)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Số điện thoại {clean_phone} đã tồn tại trong hệ thống (Khách hàng: {existing.full_name})",
            )

        cust = Customer(
            full_name=data.full_name.strip(),
            phone=clean_phone,
            email=data.email.strip() if data.email else None,
            date_of_birth=data.date_of_birth,
            default_address=data.default_address.strip() if data.default_address else None,
            source=data.source or "ONLINE",
            segment=CustomerSegment.NEW.value,
            tags=data.tags or [],
            notes=data.notes,
            consent_marketing=data.consent_marketing,
            order_count=0,
            total_spent=0.0,
            average_order_value=0.0,
            loyalty_points=0,
        )
        db.add(cust)
        await db.flush()
        return cust

    @staticmethod
    async def update_customer(
        db: AsyncSession,
        customer_id: str,
        data: CustomerUpdateInput,
    ) -> Customer:
        cust = await CustomerService.get_by_id(db, customer_id)
        if data.full_name is not None:
            cust.full_name = data.full_name.strip()
        if data.email is not None:
            cust.email = data.email.strip() if data.email else None
        if data.date_of_birth is not None:
            cust.date_of_birth = data.date_of_birth
        if data.default_address is not None:
            cust.default_address = data.default_address.strip() if data.default_address else None
        if data.tags is not None:
            cust.tags = data.tags
        if data.notes is not None:
            cust.notes = data.notes
        if data.consent_marketing is not None:
            cust.consent_marketing = data.consent_marketing
        if data.segment is not None:
            cust.segment = data.segment
        await db.flush()
        return cust

    @staticmethod
    async def sync_customer_from_order(
        db: AsyncSession,
        order: Order,
    ) -> Customer:
        """
        Synchronizes order stats into customer profile:
        - Creates or finds customer by phone
        - Links order.customer_id
        - Increments order count and accumulates total spend
        - Calculates authoritative AOV
        - Automatically earns loyalty points (1 pt per 10,000 VND)
        - Updates RFM segment dynamically
        """
        phone = order.customer_phone
        if not phone:
            return None

        cust = await CustomerService.get_or_create_by_phone(
            db=db,
            phone=phone,
            full_name=order.customer_name or "Khách hàng",
            email=order.customer_email,
            address=order.delivery_address,
            source=order.source or "ONLINE",
        )

        # Link order to customer
        order.customer_id = cust.id

        # Update metrics
        cust.order_count = (cust.order_count or 0) + 1
        order_amount = float(order.total_amount or 0.0)
        cust.total_spent = float(cust.total_spent or 0.0) + order_amount
        if cust.order_count > 0:
            cust.average_order_value = cust.total_spent / cust.order_count

        order_time = order.created_at or utc_now()
        if not cust.first_order_at:
            cust.first_order_at = order_time
        cust.last_order_at = order_time

        # Loyalty points: 1 point per 10,000 VND spent
        earned_pts = int(order_amount // 10000)
        if earned_pts > 0:
            cust.loyalty_points = (cust.loyalty_points or 0) + earned_pts
            tx = LoyaltyTransaction(
                customer_id=cust.id,
                order_id=order.id,
                transaction_type=LoyaltyTransactionType.EARN.value,
                points=earned_pts,
                balance_after=cust.loyalty_points,
                reason=f"Tích điểm từ đơn hàng #{order.order_number} (+{earned_pts} Mộc Xu)",
            )
            db.add(tx)

        # Dynamic RFM Segment calculation
        cust.segment = calculate_rfm_segment(
            order_count=cust.order_count,
            total_spent=cust.total_spent,
            last_order_at=cust.last_order_at,
            aov=cust.average_order_value,
        )

        await db.flush()
        return cust

    @staticmethod
    async def adjust_loyalty_points(
        db: AsyncSession,
        customer_id: str,
        points: int,
        reason: str,
        user_id: Optional[str] = None,
    ) -> LoyaltyTransaction:
        cust = await CustomerService.get_by_id(db, customer_id)
        current_pts = cust.loyalty_points or 0
        new_balance = current_pts + points
        if new_balance < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Số điểm tích lũy hiện tại ({current_pts}) không đủ để trừ {abs(points)} điểm.",
            )

        cust.loyalty_points = new_balance
        tx_type = (
            LoyaltyTransactionType.ADJUSTMENT.value
            if points > 0
            else LoyaltyTransactionType.REDEEM.value
        )
        tx = LoyaltyTransaction(
            customer_id=cust.id,
            transaction_type=tx_type,
            points=points,
            balance_after=new_balance,
            reason=reason,
            created_by_user_id=user_id,
        )
        db.add(tx)
        await db.flush()
        return tx

    @staticmethod
    async def list_customers(
        db: AsyncSession,
        segment: Optional[str] = None,
        search: Optional[str] = None,
        tag: Optional[str] = None,
        sort_by: str = "created_at_desc",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Customer], int]:
        stmt = select(Customer)

        if segment:
            stmt = stmt.where(Customer.segment == segment)

        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Customer.full_name.ilike(term),
                    Customer.phone.ilike(term),
                    Customer.email.ilike(term),
                )
            )

        if tag:
            # Check JSON array
            stmt = stmt.where(func.json_extract(Customer.tags, '$').like(f"%{tag.strip()}%"))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_res = await db.execute(count_stmt)
        total = total_res.scalar_one()

        if sort_by == "total_spent_desc":
            stmt = stmt.order_by(desc(Customer.total_spent))
        elif sort_by == "order_count_desc":
            stmt = stmt.order_by(desc(Customer.order_count))
        elif sort_by == "last_order_desc":
            stmt = stmt.order_by(desc(Customer.last_order_at))
        else:
            stmt = stmt.order_by(desc(Customer.created_at))

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        res = await db.execute(stmt)
        items = list(res.scalars().all())
        return items, total

    @staticmethod
    async def get_customer_360(
        db: AsyncSession,
        customer_id: str,
    ) -> Customer360Response:
        cust = await CustomerService.get_by_id(db, customer_id)

        # 1. Fetch recent orders
        orders_stmt = (
            select(Order)
            .where(
                or_(
                    Order.customer_id == cust.id,
                    Order.customer_phone == cust.phone,
                )
            )
            .order_by(desc(Order.created_at))
            .limit(15)
        )
        orders_res = await db.execute(orders_stmt)
        recent_orders_list = list(orders_res.scalars().all())

        order_summaries = [
            CustomerOrderSummary(
                id=o.id,
                order_number=o.order_number,
                status=o.status.value if hasattr(o.status, 'value') else str(o.status),
                payment_status=o.payment_status.value if hasattr(o.payment_status, 'value') else str(o.payment_status),
                total_amount=float(o.total_amount),
                items_count=o.items_count,
                source=o.source,
                created_at=o.created_at,
            )
            for o in recent_orders_list
        ]

        # 2. Favorite products and categories analysis
        order_ids = [o.id for o in recent_orders_list]
        favorite_products = []
        most_used_channel = cust.source or "ONLINE"

        if order_ids:
            items_stmt = select(OrderItem).where(OrderItem.order_id.in_(order_ids))
            items_res = await db.execute(items_stmt)
            order_items = list(items_res.scalars().all())

            product_aggregates: Dict[str, Dict[str, Any]] = {}
            for item in order_items:
                name = item.product_name
                if name not in product_aggregates:
                    product_aggregates[name] = {"quantity": 0, "total": 0.0}
                product_aggregates[name]["quantity"] += item.quantity
                product_aggregates[name]["total"] += float(item.subtotal)

            sorted_prods = sorted(
                product_aggregates.items(),
                key=lambda x: x[1]["quantity"],
                reverse=True,
            )[:5]

            favorite_products = [
                FavoriteProductItem(
                    product_name=p[0],
                    quantity_bought=p[1]["quantity"],
                    total_spent=p[1]["total"],
                )
                for p in sorted_prods
            ]

            # Most used channel
            channel_counts: Dict[str, int] = {}
            for o in recent_orders_list:
                ch = o.source or "ONLINE"
                channel_counts[ch] = channel_counts.get(ch, 0) + 1
            if channel_counts:
                most_used_channel = max(channel_counts.items(), key=lambda x: x[1])[0]

        # 3. Recent loyalty transactions
        tx_stmt = (
            select(LoyaltyTransaction)
            .where(LoyaltyTransaction.customer_id == cust.id)
            .order_by(desc(LoyaltyTransaction.created_at))
            .limit(10)
        )
        tx_res = await db.execute(tx_stmt)
        tx_list = list(tx_res.scalars().all())

        loyalty_summaries = [
            LoyaltyTransactionResponse(
                id=t.id,
                customer_id=t.customer_id,
                order_id=t.order_id,
                transaction_type=t.transaction_type,
                points=t.points,
                balance_after=t.balance_after,
                reason=t.reason,
                created_by_user_id=t.created_by_user_id,
                created_at=t.created_at,
            )
            for t in tx_list
        ]

        days_since_last = None
        if cust.last_order_at:
            now = utc_now()
            last_dt = cust.last_order_at.replace(tzinfo=timezone.utc) if cust.last_order_at.tzinfo is None else cust.last_order_at
            days_since_last = max(0, (now - last_dt).days)

        return Customer360Response(
            id=cust.id,
            full_name=cust.full_name,
            phone=cust.phone,
            email=cust.email,
            date_of_birth=cust.date_of_birth,
            default_address=cust.default_address,
            source=cust.source,
            segment=cust.segment,
            order_count=cust.order_count or 0,
            total_spent=float(cust.total_spent or 0.0),
            average_order_value=float(cust.average_order_value or 0.0),
            loyalty_points=cust.loyalty_points or 0,
            tags=cust.tags or [],
            notes=cust.notes,
            consent_marketing=cust.consent_marketing,
            first_order_at=cust.first_order_at,
            last_order_at=cust.last_order_at,
            days_since_last_order=days_since_last,
            most_used_channel=most_used_channel,
            favorite_products=favorite_products,
            recent_orders=order_summaries,
            recent_loyalty_transactions=loyalty_summaries,
            created_at=cust.created_at,
        )

    @staticmethod
    async def get_overview_stats(db: AsyncSession) -> CustomerOverviewStats:
        # Total customers
        total_res = await db.execute(select(func.count(Customer.id)))
        total_customers = total_res.scalar_one() or 0

        # VIP customers
        vip_res = await db.execute(
            select(func.count(Customer.id)).where(Customer.segment == CustomerSegment.VIP.value)
        )
        vip_customers = vip_res.scalar_one() or 0

        # At risk customers
        at_risk_res = await db.execute(
            select(func.count(Customer.id)).where(
                or_(
                    Customer.segment == CustomerSegment.AT_RISK.value,
                    Customer.segment == CustomerSegment.DORMANT.value,
                )
            )
        )
        at_risk_customers = at_risk_res.scalar_one() or 0

        # New this month
        now = utc_now()
        start_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        new_res = await db.execute(
            select(func.count(Customer.id)).where(Customer.created_at >= start_of_month)
        )
        new_this_month = new_res.scalar_one() or 0

        # Total points circulating
        pts_res = await db.execute(select(func.sum(Customer.loyalty_points)))
        total_pts = pts_res.scalar_one() or 0

        # Average LTV (total spent / total customers)
        spent_res = await db.execute(select(func.sum(Customer.total_spent)))
        total_spent = spent_res.scalar_one() or 0.0
        avg_ltv = float(total_spent) / total_customers if total_customers > 0 else 0.0

        return CustomerOverviewStats(
            total_customers=total_customers,
            vip_customers=vip_customers,
            new_customers_this_month=new_this_month,
            at_risk_customers=at_risk_customers,
            total_loyalty_points_circulating=int(total_pts),
            average_ltv=avg_ltv,
        )
