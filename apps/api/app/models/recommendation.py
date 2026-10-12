import enum
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    String,
    Text,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RecommendationType(str, enum.Enum):
    INVENTORY_CLEARANCE = "INVENTORY_CLEARANCE"
    CAMPAIGN_OPPORTUNITY = "CAMPAIGN_OPPORTUNITY"
    CUSTOMER_RETENTION = "CUSTOMER_RETENTION"
    CHANNEL_OPTIMIZATION = "CHANNEL_OPTIMIZATION"
    PRICE_PROMO_STRATEGY = "PRICE_PROMO_STRATEGY"


class RecommendationStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DISMISSED = "DISMISSED"
    APPLIED = "APPLIED"


class ConfidenceLevel(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AlertSeverity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class AlertStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class AlertType(str, enum.Enum):
    EXPIRY_RISK = "EXPIRY_RISK"
    LOW_STOCK = "LOW_STOCK"
    HIGH_WASTE = "HIGH_WASTE"
    ROAS_DROP = "ROAS_DROP"
    LOW_MARGIN_RISK = "LOW_MARGIN_RISK"
    REVENUE_ANOMALY = "REVENUE_ANOMALY"


class AIRecommendation(Base):
    """
    Khuyến nghị kinh doanh và tiếp thị sinh bởi AI dựa trên bằng chứng dữ liệu thực tế (Evidence-based).
    Tuân thủ nguyên tắc không bịa đặt số liệu: Mọi con số đều được truy xuất từ cơ sở dữ liệu.
    """
    __tablename__ = "ai_recommendations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    recommendation_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(50), default=RecommendationStatus.PENDING.value, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    problem_statement: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)

    # Danh sách bằng chứng số học thực tế từ DB:
    # [{"metric": "Tồn kho cận date", "value": "45 phần", "comparison": "Hạn dùng còn < 3 ngày", "source": "inventory_batches"}]
    evidence: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    # Thông tin bổ trợ mục tiêu
    target_products: Mapped[list] = mapped_column(JSON, default=list)  # [{"id": "...", "name": "...", "sku": "..."}]
    target_customer_segment: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    target_channels: Mapped[list] = mapped_column(JSON, default=list)  # ["WEBSITE_BANNER", "ZALO"]
    suggested_promotion: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {"promo_type": "...", "discount_value": 25}
    expected_impact: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {"estimated_revenue": 1500000, "waste_prevented": 30}

    # Đánh giá độ tin cậy
    confidence_score: Mapped[float] = mapped_column(Float, default=0.85)
    confidence_level: Mapped[str] = mapped_column(
        String(20), default=ConfidenceLevel.HIGH.value, index=True
    )
    risks: Mapped[list] = mapped_column(JSON, default=list)  # ["Giảm nhẹ biên lợi nhuận", ...]
    dismiss_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 1-Click Convert references
    converted_campaign_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True, index=True
    )
    converted_workflow_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("automation_workflows.id", ondelete="SET NULL"), nullable=True, index=True
    )

    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    applied_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    __table_args__ = (
        Index("ix_ai_rec_type_status", "recommendation_type", "status"),
        Index("ix_ai_rec_conf_status", "confidence_level", "status"),
    )


class SmartAlert(Base):
    """
    Cảnh báo thông minh thời gian thực về rủi ro vận hành, kho hàng, chi phí quảng cáo và biên lợi nhuận sàn.
    """
    __tablename__ = "smart_alerts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(
        String(20), default=AlertSeverity.WARNING.value, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default=AlertStatus.ACTIVE.value, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # PRODUCT, INVENTORY_BATCH, CAMPAIGN, CHANNEL
    entity_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    metric_data: Mapped[dict] = mapped_column(JSON, default=dict)
    action_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    acknowledged_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resolved_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        Index("ix_smart_alert_sev_status", "severity", "status"),
        Index("ix_smart_alert_type_status", "alert_type", "status"),
    )
