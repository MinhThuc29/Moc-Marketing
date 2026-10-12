import enum
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    String,
    Text,
    Integer,
    Numeric,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


class MarketplaceChannel(str, enum.Enum):
    WEBSITE = "WEBSITE"
    GRAB = "GRAB"
    SHOPEEFOOD = "SHOPEEFOOD"
    ZALO = "ZALO"
    FACEBOOK = "FACEBOOK"
    TIKTOK = "TIKTOK"
    POS = "POS"
    MANUAL = "MANUAL"


class ImportStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ReconciliationStatus(str, enum.Enum):
    UNMATCHED = "UNMATCHED"
    PARTIAL = "PARTIAL"
    MATCHED = "MATCHED"
    DISPUTED = "DISPUTED"


class MarketplaceImport(Base):
    __tablename__ = "marketplace_imports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    channel: Mapped[str] = mapped_column(String(50), default=MarketplaceChannel.GRAB.value, index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_format: Mapped[str] = mapped_column(String(20), default="CSV", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=ImportStatus.COMPLETED.value, index=True, nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    imported_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejected_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    gross_amount_total: Mapped[float] = mapped_column(Numeric(14, 2), default=0.0, nullable=False)
    platform_fee_total: Mapped[float] = mapped_column(Numeric(14, 2), default=0.0, nullable=False)
    merchant_discount_total: Mapped[float] = mapped_column(Numeric(14, 2), default=0.0, nullable=False)
    net_settlement_total: Mapped[float] = mapped_column(Numeric(14, 2), default=0.0, nullable=False)
    error_report_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    orders: Mapped[List["Order"]] = relationship(
        "Order",
        back_populates="marketplace_import",
        foreign_keys="Order.raw_import_id",
    )


class Settlement(Base):
    __tablename__ = "settlements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    channel: Mapped[str] = mapped_column(String(50), default=MarketplaceChannel.GRAB.value, index=True, nullable=False)
    external_settlement_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    gross_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0.0, nullable=False)
    platform_fee: Mapped[float] = mapped_column(Numeric(14, 2), default=0.0, nullable=False)
    merchant_discount: Mapped[float] = mapped_column(Numeric(14, 2), default=0.0, nullable=False)
    other_fee: Mapped[float] = mapped_column(Numeric(14, 2), default=0.0, nullable=False)
    net_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default=ReconciliationStatus.UNMATCHED.value, index=True, nullable=False
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    settlement_orders: Mapped[List["SettlementOrder"]] = relationship(
        "SettlementOrder",
        back_populates="settlement",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class SettlementOrder(Base):
    __tablename__ = "settlement_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    settlement_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("settlements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    allocated_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    platform_fee: Mapped[float] = mapped_column(Numeric(14, 2), default=0.0, nullable=False)
    merchant_discount: Mapped[float] = mapped_column(Numeric(14, 2), default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="MATCHED", nullable=False)
    matched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    settlement: Mapped["Settlement"] = relationship("Settlement", back_populates="settlement_orders")
    order: Mapped["Order"] = relationship("Order", lazy="selectin")
