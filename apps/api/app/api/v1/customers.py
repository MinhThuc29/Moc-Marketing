import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, require_permission
from app.models.auth import User
from app.schemas.customer import (
    CustomerCreateInput,
    CustomerUpdateInput,
    CustomerListItem,
    CustomerListResponse,
    Customer360Response,
    LoyaltyTransactionResponse,
    LoyaltyAdjustRequest,
    CustomerOverviewStats,
)
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customer CRM & Loyalty"])


@router.get("/overview", response_model=CustomerOverviewStats)
async def get_crm_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("customer.read")),
):
    """
    Get CRM summary overview metrics (total customers, VIP, At-risk, circulating points, LTV).
    """
    return await CustomerService.get_overview_stats(db)


@router.get("", response_model=CustomerListResponse)
async def list_customers(
    segment: Optional[str] = Query(None, description="Filter by RFM segment"),
    search: Optional[str] = Query(None, description="Search by name, phone, or email"),
    tag: Optional[str] = Query(None, description="Filter by customer tag"),
    sort_by: str = Query("created_at_desc", description="Sort option"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("customer.read")),
):
    """
    List customers with pagination, RFM segment filtering, search, and sorting.
    """
    items, total = await CustomerService.list_customers(
        db=db,
        segment=segment,
        search=search,
        tag=tag,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return CustomerListResponse(
        items=[CustomerListItem.model_validate(it) for it in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{customer_id}", response_model=CustomerListItem)
async def get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("customer.read")),
):
    """
    Get single customer profile by ID.
    """
    cust = await CustomerService.get_by_id(db, customer_id)
    return CustomerListItem.model_validate(cust)


@router.post("", response_model=CustomerListItem, status_code=status.HTTP_201_CREATED)
async def create_customer(
    payload: CustomerCreateInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("customer.write")),
):
    """
    Create customer profile manually.
    """
    cust = await CustomerService.create_customer(db, payload)
    await db.commit()
    await db.refresh(cust)
    return CustomerListItem.model_validate(cust)


@router.put("/{customer_id}", response_model=CustomerListItem)
async def update_customer(
    customer_id: str,
    payload: CustomerUpdateInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("customer.write")),
):
    """
    Update customer profile, notes, marketing consent, or tags.
    """
    cust = await CustomerService.update_customer(db, customer_id, payload)
    await db.commit()
    await db.refresh(cust)
    return CustomerListItem.model_validate(cust)


@router.get("/{customer_id}/360", response_model=Customer360Response)
async def get_customer_360_view(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("customer.read")),
):
    """
    Get complete Customer 360 view (Profile, recent orders, favorite products, channel, points ledger).
    """
    return await CustomerService.get_customer_360(db, customer_id)


@router.post("/{customer_id}/loyalty/adjust", response_model=LoyaltyTransactionResponse)
async def adjust_loyalty_points(
    customer_id: str,
    payload: LoyaltyAdjustRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("customer.write")),
):
    """
    Manually add or deduct loyalty points (Mộc Xu) for a customer with audit reason.
    """
    tx = await CustomerService.adjust_loyalty_points(
        db=db,
        customer_id=customer_id,
        points=payload.points,
        reason=payload.reason,
        user_id=current_user.id,
    )
    await db.commit()
    await db.refresh(tx)
    return LoyaltyTransactionResponse.model_validate(tx)
