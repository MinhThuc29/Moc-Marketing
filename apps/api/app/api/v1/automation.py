from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, require_permission
from app.models.auth import User
from app.schemas.automation import (
    WorkflowCreateInput,
    WorkflowUpdateInput,
    WorkflowStatusUpdateInput,
    WorkflowListItem,
    WorkflowDetailResponse,
    WorkflowListResponse,
    AutomationOverviewStats,
    AutomationRunListItem,
    AutomationRunDetailResponse,
    AutomationRunListResponse,
    TriggerDispatchInput,
    TriggerDispatchResult,
    TestRunInput,
    TestRunResult,
)
from app.services.automation_service import AutomationService

router = APIRouter(prefix="/automation", tags=["Marketing Automation & Customer Journeys"])


@router.get("/overview", response_model=AutomationOverviewStats)
async def get_automation_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Thống kê tổng quan Marketing Automation Hub:
    Tổng kịch bản, đang hoạt động, tạm dừng, tổng lượt thực thi, tỷ lệ thành công %, số template hệ thống.
    """
    return await AutomationService.get_overview_stats(db)


@router.get("/workflows", response_model=WorkflowListResponse)
async def list_workflows(
    trigger_type: Optional[str] = Query(None, description="Lọc theo loại trigger"),
    status: Optional[str] = Query(None, description="Lọc theo trạng thái"),
    search: Optional[str] = Query(None, description="Tìm theo tên hoặc mã kịch bản"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lấy danh sách các kịch bản tự động hóa với bộ lọc trigger, trạng thái và phân trang.
    """
    return await AutomationService.list_workflows(
        db=db,
        trigger_type=trigger_type,
        status_filter=status,
        search=search,
        page=page,
        limit=limit,
    )


@router.get("/workflows/{id}", response_model=WorkflowDetailResponse)
async def get_workflow_detail(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lấy thông tin chi tiết cấu hình kịch bản và 10 lượt chạy gần nhất.
    """
    return await AutomationService.get_workflow_detail(db, id)


@router.post("/workflows", response_model=WorkflowListItem, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    payload: WorkflowCreateInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Tạo kịch bản tự động hóa mới (yêu cầu quyền quản lý chiến dịch hoặc cài đặt).
    """
    return await AutomationService.create_workflow(db, payload, user_id=current_user.id)


@router.put("/workflows/{id}", response_model=WorkflowListItem)
async def update_workflow(
    id: str,
    payload: WorkflowUpdateInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cập nhật cấu hình kịch bản tự động hóa (Tên, Trigger, Điều kiện, Hành động).
    """
    return await AutomationService.update_workflow(db, id, payload)


@router.patch("/workflows/{id}/status", response_model=WorkflowListItem)
async def toggle_workflow_status(
    id: str,
    payload: WorkflowStatusUpdateInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Bật / Tắt trạng thái vận hành của kịch bản (ACTIVE, PAUSED, DRAFT, ARCHIVED).
    """
    return await AutomationService.toggle_workflow_status(db, id, payload.status)


@router.delete("/workflows/{id}", status_code=status.HTTP_200_OK)
async def delete_workflow(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Xóa kịch bản tự động hóa (không cho phép xóa kịch bản hệ thống mặc định).
    """
    await AutomationService.delete_workflow(db, id)
    return {"message": "Đã xóa kịch bản tự động hóa thành công"}


@router.post("/workflows/{id}/test-run", response_model=TestRunResult)
async def test_run_workflow(
    id: str,
    payload: TestRunInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Thực hiện chạy thử nghiệm giả lập (Dry-run test) kịch bản tự động hóa với dữ liệu mẫu
    để kiểm tra các điều kiện (Conditions) và hành động (Actions) mà không làm thay đổi dữ liệu thật.
    """
    return await AutomationService.test_run_workflow(db, id, payload.test_context)


@router.get("/runs", response_model=AutomationRunListResponse)
async def list_runs(
    workflow_id: Optional[str] = Query(None, description="Lọc theo workflow cụ thể"),
    status: Optional[str] = Query(None, description="Lọc theo trạng thái RUNNING, SUCCESS, FAILED"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lấy danh sách nhật ký thực thi (Audit Run Logs) của toàn bộ các kịch bản tự động hóa.
    """
    return await AutomationService.list_runs(
        db=db,
        workflow_id=workflow_id,
        status_filter=status,
        page=page,
        limit=limit,
    )


@router.get("/runs/{id}", response_model=AutomationRunDetailResponse)
async def get_run_detail(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lấy chi tiết từng bước thực thi (step_runs) và ngữ cảnh của một lượt chạy cụ thể.
    """
    return await AutomationService.get_run_detail(db, id)


@router.post("/triggers/dispatch", response_model=TriggerDispatchResult)
async def dispatch_trigger(
    payload: TriggerDispatchInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Điểm tiếp nhận sự kiện kích hoạt tự động hóa (Event Trigger Dispatcher):
    Nhận trigger_type (CUSTOMER_CREATED, CART_ABANDONED, ORDER_COMPLETED, v.v.),
    so khớp các kịch bản ACTIVE, đánh giá điều kiện và thực thi tuần tự các hành động.
    """
    return await AutomationService.dispatch_trigger(
        db=db,
        trigger_type=payload.trigger_type,
        source_id=payload.source_id,
        context=payload.context,
    )
