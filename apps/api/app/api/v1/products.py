from math import ceil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import require_permission
from app.models.auth import User
from app.models.product import Product, Category, PriceAuditLog, ProductStatus, utc_now
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductDetailResponse,
    ProductListResponse,
    PriceAuditLogResponse,
    BulkStatusUpdateRequest,
)
from app.core.utils import slugify_vn

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=ProductListResponse)
async def list_products(
    q: Optional[str] = Query(None, description="Tìm kiếm theo tên sản phẩm hoặc mã SKU"),
    category_id: Optional[str] = Query(None, description="Lọc theo ID danh mục"),
    status: Optional[ProductStatus] = Query(None, description="Lọc theo trạng thái"),
    featured: Optional[bool] = Query(None, description="Lọc sản phẩm nổi bật"),
    sort_by: str = Query("created_at_desc", description="Tiêu chí sắp xếp"),
    page: int = Query(1, ge=1, description="Số trang (bắt đầu từ 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Số lượng mục trên mỗi trang"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("product.read")),
):
    stmt = select(Product).options(selectinload(Product.category))

    # Filters
    if q and q.strip():
        search_pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Product.name.ilike(search_pattern),
                Product.sku.ilike(search_pattern),
            )
        )

    if category_id:
        stmt = stmt.where(Product.category_id == category_id)

    if status:
        stmt = stmt.where(Product.status == status.value)

    if featured is not None:
        stmt = stmt.where(Product.featured == featured)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one() or 0

    # Sorting
    if sort_by == "created_at_asc":
        stmt = stmt.order_by(Product.created_at.asc())
    elif sort_by == "price_asc":
        stmt = stmt.order_by(Product.base_price.asc())
    elif sort_by == "price_desc":
        stmt = stmt.order_by(Product.base_price.desc())
    elif sort_by == "name_asc":
        stmt = stmt.order_by(Product.name.asc())
    elif sort_by == "name_desc":
        stmt = stmt.order_by(Product.name.desc())
    else:  # default created_at_desc
        stmt = stmt.order_by(Product.created_at.desc())

    # Pagination
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    products = result.scalars().all()

    total_pages = ceil(total / page_size) if total > 0 else 1

    return ProductListResponse(
        items=products,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.patch("/bulk-status")
async def bulk_update_product_status(
    payload: BulkStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("product.write")),
):
    if not payload.ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Danh sách ID sản phẩm không được rỗng",
        )

    stmt = (
        update(Product)
        .where(Product.id.in_(payload.ids))
        .values(status=payload.status.value, updated_at=utc_now())
    )
    result = await db.execute(stmt)
    await db.commit()

    return {
        "success": True,
        "updated_count": result.rowcount,
        "status": payload.status.value,
    }


@router.get("/{id_or_slug}", response_model=ProductDetailResponse)
async def get_product(
    id_or_slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("product.read")),
):
    stmt = (
        select(Product)
        .options(
            selectinload(Product.category),
            selectinload(Product.price_logs),
        )
        .where((Product.id == id_or_slug) | (Product.slug == id_or_slug))
    )
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy thông tin sản phẩm",
        )

    return product


@router.get("/{product_id}/price-history", response_model=List[PriceAuditLogResponse])
async def get_product_price_history(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("product.read")),
):
    # Verify product exists
    prod_res = await db.execute(select(Product.id).where(Product.id == product_id))
    if not prod_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy sản phẩm",
        )

    stmt = (
        select(PriceAuditLog)
        .where(PriceAuditLog.product_id == product_id)
        .order_by(PriceAuditLog.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("product.write")),
):
    # Check SKU uniqueness
    sku = payload.sku.strip().upper()
    existing_sku = await db.execute(select(Product).where(Product.sku == sku))
    if existing_sku.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Mã SKU '{sku}' đã tồn tại trong hệ thống",
        )

    # Generate or validate slug
    slug = payload.slug.strip() if payload.slug else slugify_vn(payload.name)
    if not slug:
        slug = slugify_vn(payload.name)

    existing_slug = await db.execute(select(Product).where(Product.slug == slug))
    if existing_slug.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Slug sản phẩm '{slug}' đã tồn tại",
        )

    # Validate category if provided
    if payload.category_id:
        cat_res = await db.execute(select(Category).where(Category.id == payload.category_id))
        if not cat_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Danh mục với ID '{payload.category_id}' không tồn tại",
            )

    # Price validation: sale_price <= base_price
    if payload.sale_price is not None and payload.sale_price > payload.base_price:
        raise HTTPException(
            status_code=422,
            detail="Giá khuyến mãi (sale_price) không được lớn hơn giá gốc (base_price)",
        )

    product = Product(
        sku=sku,
        slug=slug,
        name=payload.name,
        short_description=payload.short_description,
        description=payload.description,
        category_id=payload.category_id,
        base_price=payload.base_price,
        sale_price=payload.sale_price,
        cost_price=payload.cost_price,
        unit=payload.unit,
        status=payload.status.value,
        featured=payload.featured,
        tags=payload.tags,
        ingredients=payload.ingredients,
        allergens=payload.allergens,
        nutrition_text=payload.nutrition_text,
        preparation_note=payload.preparation_note,
        storage_note=payload.storage_note,
        shelf_life=payload.shelf_life,
        thumbnail=payload.thumbnail,
        media=payload.media,
        seo_title=payload.seo_title,
        seo_description=payload.seo_description,
    )
    db.add(product)
    await db.flush()

    # Create initial price audit log
    audit_log = PriceAuditLog(
        product_id=product.id,
        old_base_price=None,
        new_base_price=payload.base_price,
        old_sale_price=None,
        new_sale_price=payload.sale_price,
        changed_by_user_id=current_user.id,
        change_reason="Khởi tạo giá ban đầu",
    )
    db.add(audit_log)

    await db.commit()
    await db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("product.write")),
):
    stmt = (
        select(Product)
        .options(selectinload(Product.category))
        .where(Product.id == product_id)
    )
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy sản phẩm để cập nhật",
        )

    update_dict = payload.model_dump(exclude_unset=True)
    change_reason = update_dict.pop("change_reason", None)

    # SKU uniqueness check if updating SKU
    if "sku" in update_dict and update_dict["sku"]:
        new_sku = update_dict["sku"].strip().upper()
        if new_sku != product.sku:
            sku_check = await db.execute(select(Product).where(Product.sku == new_sku))
            if sku_check.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Mã SKU '{new_sku}' đã tồn tại",
                )
            product.sku = new_sku

    # Slug uniqueness check if updating slug
    if "slug" in update_dict and update_dict["slug"]:
        new_slug = update_dict["slug"].strip()
        if new_slug != product.slug:
            slug_check = await db.execute(select(Product).where(Product.slug == new_slug))
            if slug_check.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Slug '{new_slug}' đã tồn tại",
                )
            product.slug = new_slug

    # Validate category if changed
    if "category_id" in update_dict and update_dict["category_id"]:
        cat_check = await db.execute(select(Category).where(Category.id == update_dict["category_id"]))
        if not cat_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Danh mục '{update_dict['category_id']}' không tồn tại",
            )

    # Price Validation & Audit Logging
    old_base_price = float(product.base_price)
    old_sale_price = float(product.sale_price) if product.sale_price is not None else None

    new_base_price = float(update_dict["base_price"]) if "base_price" in update_dict and update_dict["base_price"] is not None else old_base_price
    
    if "sale_price" in update_dict:
        new_sale_price = float(update_dict["sale_price"]) if update_dict["sale_price"] is not None else None
    else:
        new_sale_price = old_sale_price

    if new_sale_price is not None and new_sale_price > new_base_price:
        raise HTTPException(
            status_code=422,
            detail="Giá khuyến mãi (sale_price) không được lớn hơn giá gốc (base_price)",
        )

    # Check if price changed -> audit log
    price_changed = (old_base_price != new_base_price) or (old_sale_price != new_sale_price)
    if price_changed:
        audit_log = PriceAuditLog(
            product_id=product.id,
            old_base_price=old_base_price,
            new_base_price=new_base_price,
            old_sale_price=old_sale_price,
            new_sale_price=new_sale_price,
            changed_by_user_id=current_user.id,
            change_reason=change_reason or "Cập nhật giá sản phẩm",
        )
        db.add(audit_log)

    # Update other fields
    for field, val in update_dict.items():
        if field in ("sku", "slug"):
            continue
        if field == "status" and isinstance(val, ProductStatus):
            setattr(product, field, val.value)
        else:
            setattr(product, field, val)

    product.updated_at = utc_now()
    await db.commit()
    await db.refresh(product)
    return product


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    hard_delete: bool = Query(False, description="Xóa vĩnh viễn khỏi cơ sở dữ liệu nếu true"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("product.write")),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy sản phẩm để xóa",
        )

    if hard_delete:
        await db.delete(product)
        await db.commit()
        return {"success": True, "message": "Đã xóa vĩnh viễn sản phẩm khỏi hệ thống"}
    else:
        # Soft delete: update status to ARCHIVED
        product.status = ProductStatus.ARCHIVED.value
        product.updated_at = utc_now()
        await db.commit()
        return {"success": True, "message": "Đã chuyển sản phẩm sang trạng thái lưu trữ (ARCHIVED)"}
