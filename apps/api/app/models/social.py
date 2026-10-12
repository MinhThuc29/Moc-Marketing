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
    from app.models.content import ContentItem


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


class SocialPlatform(str, enum.Enum):
    FACEBOOK = "FACEBOOK"
    INSTAGRAM = "INSTAGRAM"
    TIKTOK = "TIKTOK"
    ZALO_OA = "ZALO_OA"
    WEBSITE_BLOG = "WEBSITE_BLOG"


class ConnectionStatus(str, enum.Enum):
    CONNECTED = "CONNECTED"
    EXPIRED = "EXPIRED"
    ERROR = "ERROR"
    DISCONNECTED = "DISCONNECTED"


class PublishStatus(str, enum.Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    PUBLISHING = "PUBLISHING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"


class SocialConnection(Base):
    """
    Connected social platform account credentials and connection state.
    Supports both real OAuth credentials and Sandbox / Mock accounts.
    """
    __tablename__ = "social_connections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    platform: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    app_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_connected: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=ConnectionStatus.CONNECTED.value, nullable=False, index=True)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # Relationships
    published_posts: Mapped[List["PublishedPost"]] = relationship(
        "PublishedPost",
        back_populates="connection",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_social_conn_platform_status", "platform", "status"),
    )


class PublishedPost(Base):
    """
    Record of a published post execution on external social media platforms or website.
    Maintains full queue lifecycle, idempotency guard, and retry exponential backoff telemetry.
    """
    __tablename__ = "published_posts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    content_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("content_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    connection_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("social_connections.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    channel: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    external_post_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    external_post_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    publish_status: Mapped[str] = mapped_column(String(50), default=PublishStatus.PENDING.value, index=True, nullable=False)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    payload_snapshot: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # Relationships
    content: Mapped["ContentItem"] = relationship("ContentItem", lazy="selectin")
    connection: Mapped[Optional["SocialConnection"]] = relationship("SocialConnection", back_populates="published_posts", lazy="selectin")
    metrics: Mapped[List["PostMetric"]] = relationship(
        "PostMetric",
        back_populates="published_post",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(PostMetric.recorded_at)",
    )

    __table_args__ = (
        Index("idx_pub_post_channel_status", "channel", "publish_status"),
        Index("idx_pub_post_due_pickup", "publish_status", "scheduled_at"),
        Index("idx_pub_post_retry_pickup", "publish_status", "next_retry_at"),
    )


class PostMetric(Base):
    """
    Time-series engagement metrics synced from social provider APIs.
    """
    __tablename__ = "post_metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    published_post_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("published_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True, nullable=False)
    impressions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reach: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    likes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shares: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    conversions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    raw_data_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationship
    published_post: Mapped["PublishedPost"] = relationship("PublishedPost", back_populates="metrics")
