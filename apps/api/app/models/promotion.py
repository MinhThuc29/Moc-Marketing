import enum
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Any
from sqlalchemy import (
    String,
    Text,
    Integer,
    Numeric,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


class PromotionType(str, enum.Enum):
    PERCENT_DISCOUNT = "PERCENT_DISCOUNT"
    FIXED_DISCOUNT = "FIXED_DISCOUNT"
    FLASH_SALE = "FLASH_SALE"
    BUY_X_GET_Y = "BUY_X_GET_Y"
    COMBO = "COMBO"
    FREE_SHIPPING = "FREE_SHIPPING"
    VOUCHER = "VOUCHER"


class PromotionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    EXPIRED = "EXPIRED"


class ProductScope(str, enum.Enum):
    ALL = "ALL"
    SPECIFIC_PRODUCTS = "SPECIFIC_PRODUCTS"
    SPECIFIC_CATEGORIES = "SPECIFIC_CATEGORIES"


class CustomerScope(str, enum.Enum):
    ALL = "ALL"
    NEW_CUSTOMER = "NEW_CUSTOMER"
    VIP = "VIP"


class Promotion(Base):
    __tablename__ = "promotions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    min_order_value: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    max_discount: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    product_scope: Mapped[str] = mapped_column(String(50), default=ProductScope.ALL.value, nullable=False)
    applicable_product_ids: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    applicable_category_ids: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    buy_x_get_y_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    combo_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    customer_scope: Mapped[str] = mapped_column(String(50), default=CustomerScope.ALL.value, nullable=False)
    usage_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    usage_per_customer: Mapped[Optional[int]] = mapped_column(Integer, default=1, nullable=True)
    stackable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=PromotionStatus.ACTIVE.value, index=True, nullable=False)
    created_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    usages: Mapped[List["PromotionUsage"]] = relationship(
        "PromotionUsage",
        back_populates="promotion",
        cascade="all, delete-orphan",
        order_by="desc(PromotionUsage.used_at)",
        lazy="selectin",
    )


class PromotionUsage(Base):
    __tablename__ = "promotion_usages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    promotion_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("promotions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    discount_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True, nullable=False)

    promotion = relationship("Promotion", back_populates="usages")
