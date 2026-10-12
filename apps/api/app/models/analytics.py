import enum
import uuid
from datetime import datetime, timezone
from typing import Optional, Any, TYPE_CHECKING
from sqlalchemy import (
    String,
    Text,
    Integer,
    Float,
    Numeric,
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
    from app.models.content import ContentItem
    from app.models.customer import Customer
    from app.models.order import Order


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


class TrackingEventType(str, enum.Enum):
    PAGE_VIEW = "page_view"
    PRODUCT_VIEW = "product_view"
    CATEGORY_VIEW = "category_view"
    SEARCH = "search"
    PROMOTION_VIEW = "promotion_view"
    ADD_TO_CART = "add_to_cart"
    REMOVE_FROM_CART = "remove_from_cart"
    BEGIN_CHECKOUT = "begin_checkout"
    APPLY_COUPON = "apply_coupon"
    PURCHASE = "purchase"
    CAMPAIGN_CLICK = "campaign_click"
    CONTENT_CLICK = "content_click"
    OUTBOUND_CLICK = "outbound_click"
    SOCIAL_REFERRAL = "social_referral"


class AttributionModel(str, enum.Enum):
    FIRST_TOUCH = "FIRST_TOUCH"      # 100% credit cho điểm chạm tiếp thị đầu tiên
    LAST_TOUCH = "LAST_TOUCH"        # 100% credit cho điểm chạm cuối cùng trước khi mua
    LINEAR = "LINEAR"                # Chia đều credit cho toàn bộ các điểm chạm
    TIME_DECAY = "TIME_DECAY"        # Điểm chạm càng gần đơn hàng nhận càng nhiều credit


class AttributionConfidence(str, enum.Enum):
    DETERMINISTIC = "DETERMINISTIC"  # Trực tiếp qua Session cookie / UTM tracking trên owned web
    INFERRED = "INFERRED"            # Suy luận qua mã voucher / chiến dịch / Smart link ra sàn ngoài
    AGGREGATED = "AGGREGATED"        # Đối soát báo cáo tổng hợp từ marketplace
    UNKNOWN = "UNKNOWN"              # Đơn hàng vãng lai không nhận diện được nguồn gốc


class TrackingEvent(Base):
    __tablename__ = "tracking_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    event_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    anonymous_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    customer_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    page_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    referrer: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # UTM Parameters
    utm_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    utm_medium: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    utm_campaign: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    utm_content: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    utm_term: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    channel: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)

    # Entity Associations
    product_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    order_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    campaign_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    content_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("content_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    event_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    product: Mapped[Optional["Product"]] = relationship("Product", foreign_keys=[product_id], lazy="selectin")
    campaign: Mapped[Optional["Campaign"]] = relationship("Campaign", foreign_keys=[campaign_id], lazy="selectin")
    content_item: Mapped[Optional["ContentItem"]] = relationship("ContentItem", foreign_keys=[content_id], lazy="selectin")
    customer: Mapped[Optional["Customer"]] = relationship("Customer", foreign_keys=[customer_id], lazy="selectin")

    __table_args__ = (
        Index("ix_tracking_session_time", "session_id", "created_at"),
        Index("ix_tracking_campaign_event", "campaign_id", "event_name"),
        Index("ix_tracking_channel_event", "channel", "event_name"),
    )


class ConversionAttribution(Base):
    __tablename__ = "conversion_attributions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    order_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_number: Mapped[str] = mapped_column(String(50), nullable=False)
    attribution_model: Mapped[str] = mapped_column(
        String(50),
        default=AttributionModel.LAST_TOUCH.value,
        nullable=False,
        index=True,
    )
    confidence: Mapped[str] = mapped_column(
        String(50),
        default=AttributionConfidence.DETERMINISTIC.value,
        nullable=False,
        index=True,
    )

    first_touch_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_touch_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    campaign_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    campaign_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    content_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("content_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    touchpoints_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    order_revenue: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    attributed_revenue: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    attribution_weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    touchpoint_details: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    order: Mapped["Order"] = relationship("Order", foreign_keys=[order_id], lazy="selectin")
    campaign: Mapped[Optional["Campaign"]] = relationship("Campaign", foreign_keys=[campaign_id], lazy="selectin")
    content_item: Mapped[Optional["ContentItem"]] = relationship("ContentItem", foreign_keys=[content_id], lazy="selectin")

    __table_args__ = (
        Index("ix_attr_order_model", "order_id", "attribution_model"),
        Index("ix_attr_campaign_model", "campaign_id", "attribution_model"),
    )
