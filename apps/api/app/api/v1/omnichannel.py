from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, require_permission
from app.models.auth import User
from app.services.omnichannel_service import OmnichannelService
from app.schemas.omnichannel import (
    MarketplaceImportPreviewResponse,
    MarketplaceImportExecuteRequest,
    MarketplaceImportResponse,
    SettlementCreateRequest,
    SettlementResponse,
    SettlementReconcileResult,
    OmnichannelPnLResponse,
)

router = APIRouter()


@router.post(
    "/imports/preview",
    response_model=MarketplaceImportPreviewResponse,
    summary="Xem trước dữ liệu đơn hàng sàn từ file CSV/report",
)
async def preview_marketplace_import(
    channel: str = Form(..., description="Kênh sàn (GRAB, SHOPEEFOOD, MANUAL)"),
    file: UploadFile = File(..., description="Tập tin báo cáo CSV / TXT"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("order.read")),
):
    try:
        content_bytes = await file.read()
        content = content_bytes.decode("utf-8-sig", errors="replace")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Không thể đọc nội dung file: {str(e)}")

    return await OmnichannelService.preview_import(
        session=session,
        channel=channel,
        filename=file.filename or "import.csv",
        content=content,
    )


@router.post(
    "/imports/preview-raw",
    response_model=MarketplaceImportPreviewResponse,
    summary="Xem trước dữ liệu đơn hàng sàn qua raw string",
)
async def preview_marketplace_import_raw(
    payload: MarketplaceImportExecuteRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("order.read")),
):
    return await OmnichannelService.preview_import(
        session=session,
        channel=payload.channel,
        filename=payload.filename,
        content=payload.raw_content,
    )


@router.post(
    "/imports/execute",
    response_model=MarketplaceImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Thực thi nhập đơn hàng sàn vào hệ thống",
)
async def execute_marketplace_import(
    payload: MarketplaceImportExecuteRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("order.write")),
):
    return await OmnichannelService.execute_import(
        session=session,
        user_id=current_user.id,
        channel=payload.channel,
        filename=payload.filename,
        content=payload.raw_content,
        skip_duplicates=payload.skip_duplicates,
    )


@router.get(
    "/imports",
    response_model=List[MarketplaceImportResponse],
    summary="Lịch sử các lần nhập báo cáo đơn hàng sàn",
)
async def list_marketplace_imports(
    channel: Optional[str] = Query(None, description="Lọc theo kênh"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("order.read")),
):
    return await OmnichannelService.list_imports(
        session=session,
        channel=channel,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/settlements",
    response_model=SettlementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo kỳ quyết toán từ đối tác sàn (Grab / ShopeeFood)",
)
async def create_settlement(
    payload: SettlementCreateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("order.write")),
):
    return await OmnichannelService.create_settlement(
        session=session,
        data=payload,
    )


@router.get(
    "/settlements",
    response_model=List[SettlementResponse],
    summary="Danh sách các kỳ quyết toán và trạng thái đối soát",
)
async def list_settlements(
    channel: Optional[str] = Query(None, description="Lọc theo kênh"),
    status: Optional[str] = Query(None, description="Lọc theo trạng thái (UNMATCHED, PARTIAL, MATCHED)"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("order.read")),
):
    return await OmnichannelService.list_settlements(
        session=session,
        channel=channel,
        status=status,
    )


@router.post(
    "/settlements/{settlement_id}/reconcile",
    response_model=SettlementReconcileResult,
    summary="Chạy thuật toán đối soát tự động đơn hàng với báo cáo quyết toán",
)
async def reconcile_settlement(
    settlement_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("order.write")),
):
    return await OmnichannelService.reconcile_settlement(
        session=session,
        settlement_id=settlement_id,
    )


@router.get(
    "/analytics/channel-pnl",
    response_model=OmnichannelPnLResponse,
    summary="Thống kê doanh thu, phí sàn, chiết khấu và lợi nhuận thực nhận theo từng kênh",
)
async def get_channel_pnl(
    period_start: Optional[datetime] = Query(None, description="Từ ngày"),
    period_end: Optional[datetime] = Query(None, description="Đến ngày"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("order.read")),
):
    return await OmnichannelService.get_channel_pnl(
        session=session,
        period_start=period_start,
        period_end=period_end,
    )
