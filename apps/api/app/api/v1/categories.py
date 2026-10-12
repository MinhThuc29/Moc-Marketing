from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import require_permission
from app.models.auth import User
from app.models.product import Category, Product
from app.schemas.product import CategoryCreate, CategoryUpdate, CategoryResponse
from app.core.utils import slugify_vn

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=List[CategoryResponse])
async def list_categories(
    include_inactive: bool = Query(False, description="Bao gồm cả danh mục ẩn"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("product.read")),
):
    query = select(Category).order_by(Category.sort_order.asc(), Category.name.asc())
    if not include_inactive:
        query = query.where(Category.active == True)  # noqa: E712

    result = await db.execute(query)
    categories = result.scalars().all()
    return categories


@router.get("/{id_or_slug}", response_model=CategoryResponse)
async def get_category(
    id_or_slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("product.read")),
):
    result = await db.execute(
        select(Category).where((Category.id == id_or_slug) | (Category.slug == id_or_slug))
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy danh mục",
        )
    return category


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("product.write")),
):
    slug = payload.slug.strip() if payload.slug else slugify_vn(payload.name)
    if not slug:
        slug = slugify_vn(payload.name)

    # Check slug uniqueness
    existing = await db.execute(select(Category).where(Category.slug == slug))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Slug danh mục '{slug}' đã tồn tại",
        )

    category = Category(
        name=payload.name,
        slug=slug,
        description=payload.description,
        sort_order=payload.sort_order,
        active=payload.active,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str,
    payload: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("product.write")),
):
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy danh mục để cập nhật",
        )

    update_data = payload.model_dump(exclude_unset=True)
    if "slug" in update_data and update_data["slug"]:
        new_slug = update_data["slug"].strip()
        if new_slug != category.slug:
            existing = await db.execute(select(Category).where(Category.slug == new_slug))
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Slug '{new_slug}' đã tồn tại",
                )
            category.slug = new_slug

    for field, val in update_data.items():
        if field != "slug":
            setattr(category, field, val)

    await db.commit()
    await db.refresh(category)
    return category


@router.delete("/{category_id}")
async def delete_category(
    category_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("product.write")),
):
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy danh mục để xóa",
        )

    # Detach products from this category
    products_res = await db.execute(select(Product).where(Product.category_id == category_id))
    for prod in products_res.scalars().all():
        prod.category_id = None

    await db.delete(category)
    await db.commit()
    return {"success": True, "message": "Xóa danh mục thành công"}
