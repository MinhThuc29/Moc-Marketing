import enum
import uuid
from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import (
    String,
    Text,
    Integer,
    Numeric,
    DateTime,
    ForeignKey,
    JSON,
    Boolean,
    Index,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.auth import User
    from app.models.product import Product
    from app.models.promotion import Promotion


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


class CampaignObjective(str, enum.Enum):
    AWARENESS = "AWARENESS"
    TRAFFIC = "TRAFFIC"
    CONVERSION = "CONVERSION"
    REMARKETING = "REMARKETING"
    RETENTION = "RETENTION"
    INVENTORY_CLEARANCE = "INVENTORY_CLEARANCE"
    CLEARANCE = "CLEARANCE"
    LOYALTY = "LOYALTY"
    REENGAGEMENT = "REENGAGEMENT"
    NEW_PRODUCT = "NEW_PRODUCT"


class CampaignStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PLANNING = "PLANNING"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    objective: Mapped[str] = mapped_column(
        String(50), default=CampaignObjective.CONVERSION.value, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default=CampaignStatus.DRAFT.value, index=True
    )
    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    budget: Mapped[float] = mapped_column(Numeric(14, 2), default=0.0)
    actual_spend: Mapped[float] = mapped_column(Numeric(14, 2), default=0.0)
    revenue_attributed: Mapped[float] = mapped_column(Numeric(14, 2), default=0.0)
    target_audience: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    promotion_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("promotions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    landing_page: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    utm_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    utm_medium: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    utm_campaign: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    approved_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    channels: Mapped[List["CampaignChannel"]] = relationship(
        "CampaignChannel", back_populates="campaign", cascade="all, delete-orphan"
    )
    products: Mapped[List["CampaignProduct"]] = relationship(
        "CampaignProduct", back_populates="campaign", cascade="all, delete-orphan"
    )
    promotion: Mapped[Optional["Promotion"]] = relationship(
        "Promotion", foreign_keys=[promotion_id]
    )
    created_by_user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[created_by_user_id]
    )
    approved_by_user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[approved_by_user_id]
    )


class CampaignChannel(Base):
    __tablename__ = "campaign_channels"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    campaign_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    channel_budget: Mapped[float] = mapped_column(Numeric(14, 2), default=0.0)
    channel_spend: Mapped[float] = mapped_column(Numeric(14, 2), default=0.0)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE")
    target_metric: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="channels")


class CampaignProduct(Base):
    __tablename__ = "campaign_products"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    campaign_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_hero_product: Mapped[bool] = mapped_column(Boolean, default=False)
    special_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="products")
    product: Mapped["Product"] = relationship("Product")
