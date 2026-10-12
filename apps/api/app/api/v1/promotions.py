from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import require_permission, get_current_user
from app.models.auth import User
from app.models.promotion import Promotion, PromotionStatus
from app.schemas.promotion import (
    PromotionCreateRequest,
    PromotionUpdateRequest,
    PromotionStatusUpdateRequest,
    PromotionResponse,
    PromotionListResponse,
    CalculationRequest,
    CalculationResponse,
)
from app.services.promotion_engine import (
    PromotionEngine,
    format_promotion_response,
    utc_now,
)

router = APIRouter(prefix="/promotions", tags=["Promotion Engine"])


@router.get(
    "",
    response_model=PromotionListResponse,
    dependencies=[Depends(require_permission("product.read"))],
)
async def list_promotions(
    status: Optional[str] = Query(None, description="Lọc theo trạng thái (DRAFT, ACTIVE, PAUSED, EXPIRED)"),
    type: Optional[str] = Query(None, description="Lọc theo loại khuyến mãi"),
    search: Optional[str] = Query(None, description="Tìm theo tên hoặc mã voucher"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Lấy danh sách các chương trình khuyến mãi và voucher với tìm kiếm, lọc và phân trang.
    """
    stmt = select(Promotion).order_by(desc(Promotion.created_at))

    if status:
        stmt = stmt.where(Promotion.status == status)
    if type:
        stmt = stmt.where(Promotion.type == type)
    if search and search.strip():
        s = f"%{search.strip()}%"
        stmt = stmt.where(or_(Promotion.title.ilike(s), Promotion.code.ilike(s)))

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    res = await db.execute(stmt)
    promos = list(res.scalars().all())

    now = utc_now()
    items = [format_promotion_response(p, now) for p in promos]
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PromotionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{id}",
    response_model=PromotionResponse,
    dependencies=[Depends(require_permission("product.read"))],
)
async def get_promotion_detail(
    id: str = Path(..., description="ID của chương trình khuyến mãi"),
    db: AsyncSession = Depends(get_db),
):
    """
    Xem chi tiết chương trình khuyến mãi.
    """
    res = await db.execute(select(Promotion).where(Promotion.id == id))
    promo = res.scalar_one_or_none()
    if not promo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy khuyến mãi với id: {id}",
        )
    return format_promotion_response(promo)


@router.post(
    "",
    response_model=PromotionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("campaign.create"))],
)
async def create_promotion(
    data: PromotionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Tạo mới chương trình khuyến mãi hoặc voucher.
    """
    # Check duplicate code if code is set
    if data.code:
        res_code = await db.execute(select(Promotion).where(Promotion.code == data.code))
        if res_code.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Mã khuyến mãi '{data.code}' đã tồn tại trong hệ thống.",
            )

    now = utc_now()
    promo = Promotion(
        title=data.title,
        code=data.code,
        description=data.description,
        type=data.type.value,
        value=data.value,
        min_order_value=data.min_order_value,
        max_discount=data.max_discount,
        start_at=data.start_at,
        end_at=data.end_at,
        product_scope=data.product_scope.value,
        applicable_product_ids=data.applicable_product_ids,
        applicable_category_ids=data.applicable_category_ids,
        buy_x_get_y_config=data.buy_x_get_y_config,
        combo_config=data.combo_config,
        customer_scope=data.customer_scope.value,
        usage_limit=data.usage_limit,
        usage_count=0,
        usage_per_customer=data.usage_per_customer,
        stackable=data.stackable,
        status=data.status.value,
        created_by_user_id=current_user.id,
        created_at=now,
        updated_at=now,
    )

    db.add(promo)
    await db.commit()
    await db.refresh(promo)

    return format_promotion_response(promo)


@router.put(
    "/{id}",
    response_model=PromotionResponse,
    dependencies=[Depends(require_permission("campaign.create"))],
)
async def update_promotion(
    id: str = Path(...),
    data: PromotionUpdateRequest = ...,
    db: AsyncSession = Depends(get_db),
):
    """
    Cập nhật thông tin chương trình khuyến mãi.
    """
    res = await db.execute(select(Promotion).where(Promotion.id == id))
    promo = res.scalar_one_or_none()
    if not promo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy khuyến mãi với id: {id}",
        )

    if data.code and data.code.strip().upper() != promo.code:
        code_check = data.code.strip().upper()
        res_code = await db.execute(
            select(Promotion).where(Promotion.code == code_check, Promotion.id != id)
        )
        if res_code.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Mã khuyến mãi '{code_check}' đã tồn tại.",
            )
        promo.code = code_check

    update_dict = data.model_dump(exclude_unset=True)
    if "code" in update_dict:
        del update_dict["code"]

    for k, v in update_dict.items():
        if hasattr(promo, k) and v is not None:
            if hasattr(v, "value"):
                setattr(promo, k, v.value)
            else:
                setattr(promo, k, v)

    promo.updated_at = utc_now()
    await db.commit()
    await db.refresh(promo)

    return format_promotion_response(promo)


@router.patch(
    "/{id}/status",
    response_model=PromotionResponse,
    dependencies=[Depends(require_permission("campaign.create"))],
)
async def update_promotion_status(
    id: str = Path(...),
    data: PromotionStatusUpdateRequest = ...,
    db: AsyncSession = Depends(get_db),
):
    """
    Bật/tắt trạng thái khuyến mãi (ACTIVE, PAUSED, DRAFT, EXPIRED).
    """
    res = await db.execute(select(Promotion).where(Promotion.id == id))
    promo = res.scalar_one_or_none()
    if not promo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy khuyến mãi với id: {id}",
        )

    promo.status = data.status.value
    promo.updated_at = utc_now()
    await db.commit()
    await db.refresh(promo)

    return format_promotion_response(promo)


@router.delete(
    "/{id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission("campaign.create"))],
)
async def delete_promotion(
    id: str = Path(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Xóa khuyến mãi khỏi hệ thống.
    """
    res = await db.execute(select(Promotion).where(Promotion.id == id))
    promo = res.scalar_one_or_none()
    if not promo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy khuyến mãi với id: {id}",
        )

    await db.delete(promo)
    await db.commit()
    return {"success": True, "message": "Xóa chương trình khuyến mãi thành công."}


@router.post(
    "/calculate",
    response_model=CalculationResponse,
)
async def calculate_cart_promotions(
    req: CalculationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Tính toán khuyến mãi cho giỏ hàng (Backend Authoritative Calculation).
    Client không được tự ý quyết định giá - toàn bộ chiết khấu và quà tặng được máy chủ tính toán.
    """
    return await PromotionEngine.calculate(db=db, req=req)
