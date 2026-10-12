from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.auth import User
from app.schemas.social import (
    SocialConnectionCreate,
    SocialConnectionUpdate,
    SocialConnectionResponse,
    PublishedPostResponse,
    PublishedPostListResponse,
    PostMetricResponse,
    PublishNowRequest,
    PublishNowResponse,
    WorkerBatchResult,
    ConnectionTestResult,
    TokenRefreshResult,
)
from app.services.social_service import SocialPublishingService

router = APIRouter(prefix="/social", tags=["Social Media Publishing Engine"])


# ----------------------------------------------------------------------
# 1. Social Connections Endpoints
# ----------------------------------------------------------------------

@router.get(
    "/connections",
    response_model=List[SocialConnectionResponse],
    summary="Danh sách kết nối mạng xã hội",
)
async def list_connections(
    platform: Optional[str] = Query(None, description="Lọc theo nền tảng: FACEBOOK, INSTAGRAM, TIKTOK, ZALO_OA, WEBSITE_BLOG"),
    status: Optional[str] = Query(None, description="Lọc theo trạng thái kết nối: CONNECTED, EXPIRED, ERROR, DISCONNECTED"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    connections = await SocialPublishingService.list_connections(db, platform=platform, status=status)
    return connections


@router.post(
    "/connections",
    response_model=SocialConnectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo mới hoặc kết nối tài khoản mạng xã hội",
)
async def create_connection(
    data: SocialConnectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    connection = await SocialPublishingService.create_connection(db, data)
    return connection


@router.get(
    "/connections/{id}",
    response_model=SocialConnectionResponse,
    summary="Chi tiết kết nối tài khoản",
)
async def get_connection(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = await SocialPublishingService.get_connection(db, id)
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy kết nối.")
    return conn


@router.put(
    "/connections/{id}",
    response_model=SocialConnectionResponse,
    summary="Cập nhật kết nối tài khoản",
)
async def update_connection(
    id: str,
    data: SocialConnectionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = await SocialPublishingService.update_connection(db, id, data)
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy kết nối.")
    return conn


@router.post(
    "/connections/{id}/test",
    response_model=ConnectionTestResult,
    summary="Kiểm tra kết nối tài khoản (Validate connection)",
)
async def test_connection(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    is_valid, msg, account_info = await SocialPublishingService.test_connection(db, id)
    return ConnectionTestResult(
        is_valid=is_valid,
        status="CONNECTED" if is_valid else "ERROR",
        message=msg,
        account_info=account_info,
    )


@router.post(
    "/connections/{id}/refresh",
    response_model=TokenRefreshResult,
    summary="Làm mới OAuth Token tài khoản",
)
async def refresh_token(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    success, msg, expires_at = await SocialPublishingService.refresh_connection_token(db, id)
    return TokenRefreshResult(
        success=success,
        message=msg,
        expires_at=expires_at,
    )


@router.delete(
    "/connections/{id}",
    summary="Ngắt kết nối tài khoản mạng xã hội",
)
async def disconnect_connection(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ok = await SocialPublishingService.disconnect(db, id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy kết nối.")
    return {"success": True, "message": "Đã ngắt kết nối thành công."}


# ----------------------------------------------------------------------
# 2. Publishing Execution & Logs Endpoints
# ----------------------------------------------------------------------

@router.get(
    "/published-posts",
    response_model=PublishedPostListResponse,
    summary="Danh sách lịch sử xuất bản bài viết",
)
async def list_published_posts(
    channel: Optional[str] = Query(None, description="Lọc theo kênh"),
    status: Optional[str] = Query(None, description="Lọc theo trạng thái xuất bản: PENDING, PUBLISHING, PUBLISHED, FAILED"),
    content_id: Optional[str] = Query(None, description="Lọc theo ID bài viết nội dung"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = await SocialPublishingService.list_published_posts(
        db,
        channel=channel,
        status=status,
        content_id=content_id,
        page=page,
        limit=limit,
    )

    out_items = []
    for post in items:
        resp = PublishedPostResponse.model_validate(post)
        if post.metrics:
            resp.latest_metric = PostMetricResponse.model_validate(post.metrics[0])
        out_items.append(resp)

    return PublishedPostListResponse(items=out_items, total=total)


@router.get(
    "/published-posts/{id}",
    response_model=PublishedPostResponse,
    summary="Chi tiết lượt xuất bản và telemetry",
)
async def get_published_post(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = await SocialPublishingService.get_published_post(db, id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy bản ghi xuất bản.")
    resp = PublishedPostResponse.model_validate(post)
    if post.metrics:
        resp.latest_metric = PostMetricResponse.model_validate(post.metrics[0])
    return resp


@router.post(
    "/publish-now/{content_id}",
    response_model=PublishNowResponse,
    summary="Xuất bản ngay lập tức một bài viết qua Social Engine",
)
async def publish_now(
    content_id: str,
    payload: Optional[PublishNowRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn_id = payload.connection_id if payload else None
    try:
        post = await SocialPublishingService.publish_content_now(
            db,
            content_id=content_id,
            connection_id=conn_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lỗi xuất bản: {str(e)}")

    resp = PublishedPostResponse.model_validate(post)
    if post.metrics:
        resp.latest_metric = PostMetricResponse.model_validate(post.metrics[0])

    is_success = post.publish_status == "PUBLISHED"
    msg = f"Xuất bản thành công lên kênh {post.channel}." if is_success else f"Xuất bản thất bại: {post.error_message}"

    return PublishNowResponse(
        success=is_success,
        message=msg,
        published_post=resp,
    )


@router.post(
    "/published-posts/{id}/retry",
    response_model=PublishedPostResponse,
    summary="Thử lại xuất bản thủ công bài viết bị lỗi",
)
async def retry_post(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        post = await SocialPublishingService.retry_failed_post(db, id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    resp = PublishedPostResponse.model_validate(post)
    if post.metrics:
        resp.latest_metric = PostMetricResponse.model_validate(post.metrics[0])
    return resp


@router.post(
    "/published-posts/{id}/sync-metrics",
    response_model=PostMetricResponse,
    summary="Đồng bộ tương tác mới nhất từ API mạng xã hội",
)
async def sync_metrics(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        metric = await SocialPublishingService.sync_post_metrics(db, id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return PostMetricResponse.model_validate(metric)


@router.post(
    "/worker/run-due-batch",
    response_model=WorkerBatchResult,
    summary="Kích hoạt Background Worker quét xuất bản các bài viết đến hạn",
)
async def run_worker_batch(
    limit: int = Query(10, ge=1, le=50, description="Số lượng bài viết tối đa xử lý trong batch"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await SocialPublishingService.pickup_and_publish_due_batch(db, limit=limit)
    return WorkerBatchResult(
        processed=result["processed"],
        published=result["published"],
        retried=result["retried"],
        failed=result["failed"],
        details=result["details"],
    )
