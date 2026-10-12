from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlalchemy import select, and_, or_, desc, asc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import require_permission, get_current_user
from app.models.auth import User
from app.models.inventory import InventoryBatch, InventoryMovement, BatchStatus, MovementType
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
)
from app.services.inventory_service import (
    InventoryService,
    format_batch_response,
    format_movement_response,
    utc_now,
)

router = APIRouter(prefix="/inventory", tags=["Inventory & Expiry"])


@router.get(
    "/overview",
    response_model=InventoryOverviewResponse,
    dependencies=[Depends(require_permission("inventory.read"))],
)
async def get_inventory_overview(
    db: AsyncSession = Depends(get_db),
):
    """
    Lấy thông tin tổng quan số liệu kho, giá trị tồn kho, số lô cận date và sản phẩm dưới định mức.
    """
    return await InventoryService.get_overview(db)


@router.get(
    "/products",
    response_model=List[ProductStockSummaryResponse],
    dependencies=[Depends(require_permission("inventory.read"))],
)
async def get_product_stock_summaries(
    search: Optional[str] = Query(None, description="Tìm kiếm theo tên sản phẩm hoặc mã SKU"),
    low_stock_only: bool = Query(False, description="Chỉ lấy sản phẩm dưới ngưỡng định mức tồn kho"),
    expiring_soon_only: bool = Query(False, description="Chỉ lấy sản phẩm có lô hàng sắp hết hạn (<= 3 ngày)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Lấy danh sách tồn kho tổng hợp theo từng sản phẩm F&B kèm cảnh báo hạn dùng và ngưỡng an toàn.
    """
    return await InventoryService.get_product_stock_summaries(
        db, search=search, low_stock_only=low_stock_only, expiring_soon_only=expiring_soon_only
    )


@router.get(
    "/batches",
    response_model=List[InventoryBatchResponse],
    dependencies=[Depends(require_permission("inventory.read"))],
)
async def list_batches(
    product_id: Optional[str] = Query(None, description="Lọc theo ID sản phẩm"),
    status: Optional[str] = Query(None, description="Lọc theo trạng thái lô (ACTIVE, DEPLETED, EXPIRED, v.v.)"),
    expiring_within_days: Optional[int] = Query(None, ge=1, le=90, description="Lọc lô hết hạn trong số ngày tới"),
    is_expired: Optional[bool] = Query(None, description="Lọc lô đã hết hạn"),
    search: Optional[str] = Query(None, description="Tìm theo mã lô hoặc tên sản phẩm"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """
    Danh sách các lô hàng trong kho kèm thông tin hạn dùng FEFO, số ngày còn lại và trạng thái.
    """
    now = utc_now()
    stmt = select(InventoryBatch).order_by(asc(InventoryBatch.expiry_at))

    if product_id:
        stmt = stmt.where(InventoryBatch.product_id == product_id)
    if status:
        stmt = stmt.where(InventoryBatch.status == status)

    if expiring_within_days is not None:
        target_date = now + timedelta(days=expiring_within_days)
        stmt = stmt.where(
            and_(
                InventoryBatch.expiry_at >= now,
                InventoryBatch.expiry_at <= target_date,
                InventoryBatch.quantity_available > 0,
            )
        )
    elif is_expired is True:
        stmt = stmt.where(InventoryBatch.expiry_at < now)
    elif is_expired is False:
        stmt = stmt.where(InventoryBatch.expiry_at >= now)

    if search and search.strip():
        s = f"%{search.strip()}%"
        stmt = stmt.join(InventoryBatch.product).where(
            or_(InventoryBatch.batch_code.ilike(s), InventoryBatch.product.has(name=s))
        )

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    res = await db.execute(stmt)
    batches = list(res.scalars().all())

    return [format_batch_response(b, now) for b in batches]


@router.get(
    "/batches/{id}",
    response_model=InventoryBatchResponse,
    dependencies=[Depends(require_permission("inventory.read"))],
)
async def get_batch_detail(
    id: str = Path(..., description="ID của lô hàng"),
    db: AsyncSession = Depends(get_db),
):
    """
    Xem chi tiết thông tin một lô hàng.
    """
    res = await db.execute(select(InventoryBatch).where(InventoryBatch.id == id))
    batch = res.scalar_one_or_none()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy lô hàng với id: {id}",
        )
    return format_batch_response(batch)


@router.post(
    "/batches",
    response_model=InventoryBatchResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("inventory.write"))],
)
async def receive_batch(
    data: BatchCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Nhập kho lô hàng mới (Receive stock batch). Tự động ghi nhận movement PURCHASE_IN vào sổ cái.
    """
    return await InventoryService.receive_batch(db, data, user_id=current_user.id)


@router.put(
    "/batches/{id}",
    response_model=InventoryBatchResponse,
    dependencies=[Depends(require_permission("inventory.write"))],
)
async def update_batch_info(
    id: str = Path(...),
    data: BatchUpdateRequest = ...,
    db: AsyncSession = Depends(get_db),
):
    """
    Cập nhật trạng thái hoặc ghi chú của lô hàng (không thay đổi trực tiếp số lượng).
    """
    res = await db.execute(select(InventoryBatch).where(InventoryBatch.id == id))
    batch = res.scalar_one_or_none()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy lô hàng với id: {id}",
        )

    if data.status is not None:
        batch.status = data.status.value
    if data.note is not None:
        batch.note = data.note
    if data.supplier is not None:
        batch.supplier = data.supplier

    batch.updated_at = utc_now()
    await db.commit()
    await db.refresh(batch)
    return format_batch_response(batch)


@router.post(
    "/adjustments",
    response_model=InventoryMovementResponse,
    dependencies=[Depends(require_permission("inventory.write"))],
)
async def adjust_stock(
    data: AdjustmentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Điều chỉnh số lượng tồn kho (ADJUSTMENT_IN, ADJUSTMENT_OUT, WASTE_OUT, RETURN_IN) kèm lý do bắt buộc.
    Bảo vệ chống tồn kho âm (Negative stock protection).
    """
    return await InventoryService.adjust_stock(db, data, user_id=current_user.id)


@router.get(
    "/movements",
    response_model=List[InventoryMovementResponse],
    dependencies=[Depends(require_permission("inventory.read"))],
)
async def list_movements(
    batch_id: Optional[str] = Query(None, description="Lọc theo lô hàng"),
    product_id: Optional[str] = Query(None, description="Lọc theo sản phẩm"),
    movement_type: Optional[str] = Query(None, description="Lọc theo loại biến động"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """
    Xem sổ cái luân chuyển kho (Inventory ledger) kèm người thực hiện và số dư trước/sau.
    """
    stmt = select(InventoryMovement).order_by(desc(InventoryMovement.created_at))

    if batch_id:
        stmt = stmt.where(InventoryMovement.batch_id == batch_id)
    if product_id:
        stmt = stmt.where(InventoryMovement.product_id == product_id)
    if movement_type:
        stmt = stmt.where(InventoryMovement.movement_type == movement_type)

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    res = await db.execute(stmt)
    movements = list(res.scalars().all())

    return [format_movement_response(m) for m in movements]


@router.post(
    "/fefo/simulate",
    response_model=FefoAllocationResponse,
    dependencies=[Depends(require_permission("inventory.read"))],
)
async def simulate_fefo_allocation(
    data: FefoAllocationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Mô phỏng thuật toán xuất kho FEFO (First Expired, First Out) mà không ghi giảm số lượng trong database.
    """
    return await InventoryService.fefo_allocate(db, data, dry_run=True)


@router.post(
    "/fefo/allocate",
    response_model=FefoAllocationResponse,
    dependencies=[Depends(require_permission("inventory.write"))],
)
async def execute_fefo_allocation(
    data: FefoAllocationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Thực thi phân bổ và xuất kho theo thuật toán FEFO (tạo các dòng movement SALE_OUT và trừ tồn kho các lô cận date nhất).
    """
    return await InventoryService.fefo_allocate(db, data, user_id=current_user.id, dry_run=False)


@router.get(
    "/expiry-alerts",
    response_model=List[ExpiryAlertItemResponse],
    dependencies=[Depends(require_permission("inventory.read"))],
)
async def get_expiry_alerts(
    db: AsyncSession = Depends(get_db),
):
    """
    Danh sách các lô hàng cận date có nguy cơ lãng phí (EXPIRED, CRITICAL < 24h, WARNING <= 3 ngày, ATTENTION <= 7 ngày).
    Cung cấp ước tính chi phí thất thoát làm dữ liệu đầu vào cho AI Flash Sale / Clear Stock.
    """
    return await InventoryService.get_expiry_alerts(db)
