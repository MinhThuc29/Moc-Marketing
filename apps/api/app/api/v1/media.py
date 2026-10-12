from math import ceil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import require_permission
from app.models.auth import User
from app.models.media import MediaAsset
from app.schemas.media import (
    MediaAssetResponse,
    MediaAssetListResponse,
    MediaAssetUpdate,
)
from app.core.storage import get_storage_service

router = APIRouter(prefix="/media", tags=["Media"])

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/svg+xml",
    "video/mp4",
    "video/webm",
    "video/quicktime",
}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


@router.post("/upload", response_model=List[MediaAssetResponse], status_code=status.HTTP_201_CREATED)
async def upload_media_files(
    files: List[UploadFile] = File(..., description="Danh sách tệp tải lên (ảnh/video)"),
    folder: str = Form("products", description="Thư mục phân loại (products, marketing, avatar...)"),
    tags: Optional[str] = Form(None, description="Thẻ phân loại phân cách bằng dấu phẩy"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("product.write")),
):
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không có tệp nào được gửi lên",
        )

    storage = get_storage_service()
    parsed_tags = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    created_assets = []

    for file in files:
        # Check MIME type
        content_type = file.content_type or "application/octet-stream"
        if content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Định dạng tệp '{content_type}' không được hỗ trợ. Hỗ trợ: JPG, PNG, WEBP, GIF, SVG, MP4.",
            )

        # Read file bytes
        content = await file.read()
        file_size = len(content)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Kích thước tệp '{file.filename}' ({file_size / 1024 / 1024:.1f} MB) vượt quá giới hạn tối đa 20MB",
            )

        # Upload using storage service
        upload_result = await storage.upload(
            file_bytes=content,
            original_filename=file.filename or "media",
            content_type=content_type,
            folder=folder,
        )

        asset = MediaAsset(
            filename=upload_result["filename"],
            original_name=file.filename or "media",
            mime_type=content_type,
            file_size=upload_result["file_size"],
            url=upload_result["url"],
            thumbnail_url=upload_result.get("thumbnail_url"),
            width=upload_result.get("width"),
            height=upload_result.get("height"),
            tags=parsed_tags,
            folder=folder,
            created_by_user_id=current_user.id,
        )
        db.add(asset)
        await db.flush()
        created_assets.append(asset)

    await db.commit()
    for asset in created_assets:
        await db.refresh(asset)

    return created_assets


@router.get("", response_model=MediaAssetListResponse)
async def list_media_assets(
    q: Optional[str] = Query(None, description="Tìm kiếm theo tên tệp hoặc thẻ tags"),
    folder: Optional[str] = Query(None, description="Lọc theo thư mục"),
    mime_type: Optional[str] = Query(None, description="Lọc theo kiểu mime (e.g. image/, video/)"),
    page: int = Query(1, ge=1, description="Số trang"),
    page_size: int = Query(24, ge=1, le=100, description="Số lượng mục trên mỗi trang"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("product.read")),
):
    stmt = select(MediaAsset)

    if q and q.strip():
        search_pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                MediaAsset.original_name.ilike(search_pattern),
                MediaAsset.filename.ilike(search_pattern),
            )
        )

    if folder:
        stmt = stmt.where(MediaAsset.folder == folder)

    if mime_type:
        stmt = stmt.where(MediaAsset.mime_type.ilike(f"%{mime_type}%"))

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total = total_res.scalar_one() or 0

    # Order by newest
    stmt = stmt.order_by(MediaAsset.created_at.desc())

    # Pagination
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    items = result.scalars().all()

    total_pages = ceil(total / page_size) if total > 0 else 1

    return MediaAssetListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{media_id}", response_model=MediaAssetResponse)
async def get_media_asset(
    media_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("product.read")),
):
    result = await db.execute(select(MediaAsset).where(MediaAsset.id == media_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy tệp media",
        )
    return asset


@router.put("/{media_id}", response_model=MediaAssetResponse)
async def update_media_asset(
    media_id: str,
    payload: MediaAssetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("product.write")),
):
    result = await db.execute(select(MediaAsset).where(MediaAsset.id == media_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy tệp media",
        )

    if payload.original_name is not None:
        asset.original_name = payload.original_name.strip()
    if payload.tags is not None:
        asset.tags = payload.tags
    if payload.folder is not None:
        asset.folder = payload.folder

    await db.commit()
    await db.refresh(asset)
    return asset


@router.delete("/{media_id}")
async def delete_media_asset(
    media_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("product.write")),
):
    result = await db.execute(select(MediaAsset).where(MediaAsset.id == media_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy tệp media để xóa",
        )

    # Delete physical file
    storage = get_storage_service()
    await storage.delete(asset.filename, asset.folder)

    await db.delete(asset)
    await db.commit()

    return {"success": True, "message": "Đã xóa tệp media thành công"}
