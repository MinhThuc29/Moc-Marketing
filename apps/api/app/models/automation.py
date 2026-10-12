import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    Integer,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TriggerType(str, enum.Enum):
    CUSTOMER_CREATED = "CUSTOMER_CREATED"
    CART_ABANDONED = "CART_ABANDONED"
    ORDER_COMPLETED = "ORDER_COMPLETED"
    CUSTOMER_INACTIVE = "CUSTOMER_INACTIVE"
    INVENTORY_EXPIRY_RISK = "INVENTORY_EXPIRY_RISK"
    LOW_STOCK = "LOW_STOCK"
    CAMPAIGN_ENDING = "CAMPAIGN_ENDING"


class WorkflowStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"


class RunStatus(str, enum.Enum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ActionType(str, enum.Enum):
    SEND_ZALO_MOCK = "SEND_ZALO_MOCK"
    SEND_EMAIL_MOCK = "SEND_EMAIL_MOCK"
    ISSUE_PROMOTION = "ISSUE_PROMOTION"
    ADD_LOYALTY_POINTS = "ADD_LOYALTY_POINTS"
    ADD_CUSTOMER_TAG = "ADD_CUSTOMER_TAG"
    CREATE_NOTIFICATION = "CREATE_NOTIFICATION"
    CREATE_RECOMMENDATION = "CREATE_RECOMMENDATION"
    CREATE_CAMPAIGN_DRAFT = "CREATE_CAMPAIGN_DRAFT"
    WAIT_HOURS = "WAIT_HOURS"


class AutomationWorkflow(Base):
    """
    Marketing Automation Workflow entity representing automated customer journeys
    and operational event-triggered recipes (PLAN.md Section 22 & Phase 7).
    """
    __tablename__ = "automation_workflows"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    code = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)

    trigger_type = Column(String(50), nullable=False, index=True)
    trigger_config = Column(JSON, nullable=False, default=dict)
    conditions = Column(JSON, nullable=False, default=list)
    actions = Column(JSON, nullable=False, default=list)

    status = Column(String(30), nullable=False, default=WorkflowStatus.ACTIVE.value, index=True)
    is_system_template = Column(Boolean, nullable=False, default=False)

    total_runs = Column(Integer, nullable=False, default=0)
    successful_runs = Column(Integer, nullable=False, default=0)
    failed_runs = Column(Integer, nullable=False, default=0)

    created_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    runs = relationship("AutomationRun", back_populates="workflow", cascade="all, delete-orphan", order_by="desc(AutomationRun.created_at)")
    creator = relationship("User", foreign_keys=[created_by_user_id], lazy="selectin")

    __table_args__ = (
        Index("ix_workflows_trigger_status", "trigger_type", "status"),
        Index("ix_workflows_template", "is_system_template"),
    )


class AutomationRun(Base):
    """
    Audit log record of every automated workflow execution with step-by-step telemetry.
    """
    __tablename__ = "automation_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String(36), ForeignKey("automation_workflows.id", ondelete="CASCADE"), nullable=False, index=True)

    trigger_type = Column(String(50), nullable=False)
    trigger_source_id = Column(String(100), nullable=True)

    status = Column(String(30), nullable=False, default=RunStatus.RUNNING.value, index=True)
    started_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    step_runs = Column(JSON, nullable=False, default=list)
    error_message = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    workflow = relationship("AutomationWorkflow", back_populates="runs", lazy="selectin")

    __table_args__ = (
        Index("ix_runs_wf_status", "workflow_id", "status"),
        Index("ix_runs_created_at", "created_at"),
    )
