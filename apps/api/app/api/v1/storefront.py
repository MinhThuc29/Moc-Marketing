from datetime import datetime, timezone
from math import ceil
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.product import Product, Category, ProductStatus
from app.models.promotion import Promotion, PromotionStatus
from app.schemas.storefront import (
    StorefrontCategory,
    StorefrontProduct,
    StorefrontProductDetail,
    StorefrontPromotionItem,
    StorefrontHomeResponse,
    StorefrontProductListResponse,
)

router = APIRouter(prefix="/storefront", tags=["Storefront (Public)"])


def _to_storefront_product(p: Product) -> StorefrontProduct:
    discount_pct = None
    if p.sale_price and p.sale_price < p.base_price and p.base_price > 0:
        discount_pct = int(round((p.base_price - p.sale_price) / p.base_price * 100))

    cat_name = p.category.name if p.category else None
    cat_slug = p.category.slug if p.category else None

    return StorefrontProduct(
        id=p.id,
        sku=p.sku,
        slug=p.slug,
        name=p.name,
        short_description=p.short_description,
        description=p.description,
        category_id=p.category_id,
        category_name=cat_name,
        category_slug=cat_slug,
        base_price=p.base_price,
        sale_price=p.sale_price,
        discount_percent=discount_pct,
        unit=p.unit or "phần",
        status=p.status,
        featured=p.featured,
        tags=p.tags or [],
        ingredients=p.ingredients,
        allergens=p.allergens,
        nutrition_text=p.nutrition_text,
        preparation_note=p.preparation_note,
        storage_note=p.storage_note,
        shelf_life=p.shelf_life,
        thumbnail=p.thumbnail,
        media=p.media or [],
    )


@router.get("/home", response_model=StorefrontHomeResponse)
async def get_storefront_home(db: AsyncSession = Depends(get_db)):
    """
    Public aggregated payload for Storefront Home page:
    - Banners & Vouchers
    - Active Categories
    - Featured Products
    - Categorized Product Sections
    """
    now = datetime.now(timezone.utc)

    # 1. Active promotions & vouchers
    promo_stmt = (
        select(Promotion)
        .where(
            and_(
                Promotion.status == PromotionStatus.ACTIVE.value,
                Promotion.start_at <= now,
                Promotion.end_at >= now,
            )
        )
        .order_by(Promotion.created_at.desc())
    )
    res_promos = await db.execute(promo_stmt)
    all_promos = res_promos.scalars().all()

    banners = [
        StorefrontPromotionItem.model_validate(p)
        for p in all_promos
        if p.type in ("FLASH_SALE", "FREE_SHIPPING", "PERCENT_DISCOUNT")
    ]
    active_vouchers = [
        StorefrontPromotionItem.model_validate(p)
        for p in all_promos
        if p.code is not None and len(p.code.strip()) > 0
    ]

    # 2. Categories with active product counts
    cat_stmt = select(Category).where(Category.active == True).order_by(Category.sort_order.asc())
    res_cats = await db.execute(cat_stmt)
    categories_raw = res_cats.scalars().all()

    # Product count per category
    count_stmt = (
        select(Product.category_id, func.count(Product.id))
        .where(Product.status == ProductStatus.ACTIVE.value)
        .group_by(Product.category_id)
    )
    res_counts = await db.execute(count_stmt)
    counts_map = dict(res_counts.all())

    categories = [
        StorefrontCategory(
            id=c.id,
            name=c.name,
            slug=c.slug,
            description=c.description,
            sort_order=c.sort_order,
            product_count=counts_map.get(c.id, 0),
        )
        for c in categories_raw
    ]

    # 3. Featured products
    feat_stmt = (
        select(Product)
        .options(selectinload(Product.category))
        .where(
            and_(
                Product.status == ProductStatus.ACTIVE.value,
                Product.featured == True,
            )
        )
        .order_by(Product.created_at.desc())
        .limit(8)
    )
    res_feat = await db.execute(feat_stmt)
    featured_products = [_to_storefront_product(p) for p in res_feat.scalars().all()]

    # 4. Sections by category
    category_sections: Dict[str, List[StorefrontProduct]] = {}
    for c in categories_raw[:5]:
        sec_stmt = (
            select(Product)
            .options(selectinload(Product.category))
            .where(
                and_(
                    Product.status == ProductStatus.ACTIVE.value,
                    Product.category_id == c.id,
                )
            )
            .order_by(Product.sort_order.asc() if hasattr(Product, "sort_order") else Product.created_at.desc())
            .limit(6)
        )
        res_sec = await db.execute(sec_stmt)
        prods = [_to_storefront_product(p) for p in res_sec.scalars().all()]
        if prods:
            category_sections[c.slug] = prods

    return StorefrontHomeResponse(
        banners=banners,
        categories=categories,
        featured_products=featured_products,
        category_sections=category_sections,
        active_vouchers=active_vouchers,
    )


@router.get("/products", response_model=StorefrontProductListResponse)
async def list_storefront_products(
    q: Optional[str] = Query(None, description="Tìm kiếm theo từ khóa"),
    category_slug: Optional[str] = Query(None, description="Slug danh mục"),
    category_id: Optional[str] = Query(None, description="ID danh mục"),
    tag: Optional[str] = Query(None, description="Thẻ tag"),
    featured: Optional[bool] = Query(None, description="Sản phẩm nổi bật"),
    sort_by: str = Query("newest", description="Sắp xếp: newest, price_asc, price_desc, popular"),
    page: int = Query(1, ge=1, description="Trang số"),
    page_size: int = Query(12, ge=1, le=50, description="Kích thước trang"),
    db: AsyncSession = Depends(get_db),
):
    """
    Public products search & browsing endpoint for Storefront.
    Only active products are returned.
    """
    stmt = (
        select(Product)
        .options(selectinload(Product.category))
        .where(Product.status == ProductStatus.ACTIVE.value)
    )

    if q and q.strip():
        term = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Product.name.ilike(term),
                Product.sku.ilike(term),
                Product.short_description.ilike(term),
            )
        )

    if category_slug:
        cat_sub = select(Category.id).where(Category.slug == category_slug)
        stmt = stmt.where(Product.category_id.in_(cat_sub))
    elif category_id:
        stmt = stmt.where(Product.category_id == category_id)

    if featured is not None:
        stmt = stmt.where(Product.featured == featured)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total = total_res.scalar_one()

    # Sorting
    if sort_by == "price_asc":
        stmt = stmt.order_by(Product.base_price.asc())
    elif sort_by == "price_desc":
        stmt = stmt.order_by(Product.base_price.desc())
    elif sort_by == "name_asc":
        stmt = stmt.order_by(Product.name.asc())
    else:  # newest / default
        stmt = stmt.order_by(Product.created_at.desc())

    # Pagination
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    items = [_to_storefront_product(p) for p in result.scalars().all()]
    total_pages = ceil(total / page_size) if page_size > 0 else 1

    return StorefrontProductListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/products/{slug_or_id}", response_model=StorefrontProductDetail)
async def get_storefront_product(
    slug_or_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Public product detail endpoint by slug or UUID.
    Includes related products from same category.
    """
    stmt = (
        select(Product)
        .options(selectinload(Product.category))
        .where(
            and_(
                or_(Product.id == slug_or_id, Product.slug == slug_or_id),
                Product.status == ProductStatus.ACTIVE.value,
            )
        )
    )
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy sản phẩm hoặc sản phẩm đã ngừng kinh doanh",
        )

    base_detail = _to_storefront_product(product)

    # Query related products in same category
    related_products: List[StorefrontProduct] = []
    if product.category_id:
        rel_stmt = (
            select(Product)
            .options(selectinload(Product.category))
            .where(
                and_(
                    Product.category_id == product.category_id,
                    Product.id != product.id,
                    Product.status == ProductStatus.ACTIVE.value,
                )
            )
            .limit(4)
        )
        res_rel = await db.execute(rel_stmt)
        related_products = [_to_storefront_product(p) for p in res_rel.scalars().all()]

    return StorefrontProductDetail(
        **base_detail.model_dump(),
        related_products=related_products,
    )


@router.get("/categories", response_model=List[StorefrontCategory])
async def list_storefront_categories(db: AsyncSession = Depends(get_db)):
    """
    Public categories list with product counts.
    """
    cat_stmt = select(Category).where(Category.active == True).order_by(Category.sort_order.asc())
    res_cats = await db.execute(cat_stmt)
    categories_raw = res_cats.scalars().all()

    count_stmt = (
        select(Product.category_id, func.count(Product.id))
        .where(Product.status == ProductStatus.ACTIVE.value)
        .group_by(Product.category_id)
    )
    res_counts = await db.execute(count_stmt)
    counts_map = dict(res_counts.all())

    return [
        StorefrontCategory(
            id=c.id,
            name=c.name,
            slug=c.slug,
            description=c.description,
            sort_order=c.sort_order,
            product_count=counts_map.get(c.id, 0),
        )
        for c in categories_raw
    ]


@router.get("/promotions", response_model=List[StorefrontPromotionItem])
async def list_storefront_promotions(db: AsyncSession = Depends(get_db)):
    """
    Public active promotions and vouchers for customers.
    """
    now = datetime.now(timezone.utc)
    promo_stmt = (
        select(Promotion)
        .where(
            and_(
                Promotion.status == PromotionStatus.ACTIVE.value,
                Promotion.start_at <= now,
                Promotion.end_at >= now,
            )
        )
        .order_by(Promotion.created_at.desc())
    )
    res_promos = await db.execute(promo_stmt)
    return [StorefrontPromotionItem.model_validate(p) for p in res_promos.scalars().all()]
