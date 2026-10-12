import enum
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Any
from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    Integer,
    Numeric,
    DateTime,
    ForeignKey,
    Index,
    JSON,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


class ProductStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    HIDDEN = "HIDDEN"
    ARCHIVED = "ARCHIVED"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    products: Mapped[List["Product"]] = relationship(
        "Product",
        back_populates="category",
        lazy="selectin",
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    short_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    base_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    sale_price: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    cost_price: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    unit: Mapped[str] = mapped_column(String(50), default="phần", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=ProductStatus.DRAFT.value, index=True, nullable=False)
    featured: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    tags: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    ingredients: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    allergens: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    nutrition_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preparation_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    storage_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shelf_life: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    thumbnail: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    media: Mapped[List[Any]] = mapped_column(JSON, default=list, nullable=False)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    seo_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    seo_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    category: Mapped[Optional["Category"]] = relationship(
        "Category",
        back_populates="products",
        lazy="selectin",
    )
    price_logs: Mapped[List["PriceAuditLog"]] = relationship(
        "PriceAuditLog",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="desc(PriceAuditLog.created_at)",
        lazy="selectin",
    )
    batches = relationship(
        "InventoryBatch",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class PriceAuditLog(Base):
    __tablename__ = "price_audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    old_base_price: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    new_base_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    old_sale_price: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    new_sale_price: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    changed_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    change_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
        nullable=False,
    )

    product: Mapped["Product"] = relationship("Product", back_populates="price_logs")
