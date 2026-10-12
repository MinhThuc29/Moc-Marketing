import enum
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Any, TYPE_CHECKING
from sqlalchemy import (
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.auth import User
    from app.models.product import Product
    from app.models.campaign import Campaign


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


class ContentType(str, enum.Enum):
    FACEBOOK_POST = "FACEBOOK_POST"
    INSTAGRAM_POST = "INSTAGRAM_POST"
    TIKTOK_SCRIPT = "TIKTOK_SCRIPT"
    REEL_SCRIPT = "REEL_SCRIPT"
    ZALO_MESSAGE = "ZALO_MESSAGE"
    WEBSITE_BANNER_COPY = "WEBSITE_BANNER_COPY"
    PRODUCT_STORY = "PRODUCT_STORY"
    SEO_ARTICLE = "SEO_ARTICLE"


class ContentChannel(str, enum.Enum):
    FACEBOOK = "FACEBOOK"
    INSTAGRAM = "INSTAGRAM"
    TIKTOK = "TIKTOK"
    ZALO = "ZALO"
    SMS = "SMS"
    EMAIL = "EMAIL"
    WEBSITE_BANNER = "WEBSITE_BANNER"


class ContentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    AI_GENERATED = "AI_GENERATED"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    SCHEDULED = "SCHEDULED"
    PUBLISHING = "PUBLISHING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


class BrandTone(str, enum.Enum):
    FRESH_ENERGETIC = "FRESH_ENERGETIC"          # Tươi mới, năng lượng tích cực
    NUTRITION_EXPERT = "NUTRITION_EXPERT"        # Chuyên gia dinh dưỡng tin cậy
    WARM_FRIENDLY = "WARM_FRIENDLY"              # Gần gũi, ấm áp, chăm sóc
    MINIMAL_HEALTHY = "MINIMAL_HEALTHY"          # Tối giản, thanh lọc, nhẹ nhàng
    TRENDY_HUMOR = "TRENDY_HUMOR"                # Bắt trend, trẻ trung, hóm hỉnh


class ContentItem(Base):
    __tablename__ = "content_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content_type: Mapped[str] = mapped_column(String(50), default=ContentType.FACEBOOK_POST.value, index=True, nullable=False)
    channel: Mapped[str] = mapped_column(String(50), default=ContentChannel.FACEBOOK.value, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=ContentStatus.DRAFT.value, index=True, nullable=False)
    brand_tone: Mapped[str] = mapped_column(String(50), default=BrandTone.FRESH_ENERGETIC.value, nullable=False)

    # Content structure
    hook: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Câu mở đầu giữ chân người đọc
    body: Mapped[str] = mapped_column(Text, nullable=False)                   # Nội dung chính
    cta: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)   # Lời kêu gọi hành động (Call To Action)
    hashtags: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    media_asset_ids: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)

    # Relationships
    campaign_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    product_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # AI tracking
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ai_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Publishing schedule & External tracking
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    external_post_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    external_post_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Performance metrics (views, likes, shares, comments, clicks)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Audit & Approval
    created_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # Navigation relationships
    campaign: Mapped[Optional["Campaign"]] = relationship("Campaign", lazy="selectin")
    product: Mapped[Optional["Product"]] = relationship("Product", lazy="selectin")
    created_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by_user_id],
        lazy="selectin",
    )
    approved_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[approved_by_user_id],
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_content_status_scheduled", "status", "scheduled_at"),
        Index("idx_content_channel_status", "channel", "status"),
    )
