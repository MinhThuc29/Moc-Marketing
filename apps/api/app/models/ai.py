import enum
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    JSON,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class AIProviderType(str, enum.Enum):
    MOCK = "MOCK"
    GEMINI = "GEMINI"
    OPENAI = "OPENAI"
    CLAUDE = "CLAUDE"


class AILogStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    VALIDATION_ERROR = "VALIDATION_ERROR"


class PromptCategory(str, enum.Enum):
    COPYWRITING = "COPYWRITING"
    CONTENT_STUDIO = "CONTENT_STUDIO"
    RECOMMENDATION = "RECOMMENDATION"
    CUSTOMER_SERVICE = "CUSTOMER_SERVICE"
    PRODUCT_OPTIMIZATION = "PRODUCT_OPTIMIZATION"
    GENERAL = "GENERAL"


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    slug = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False, default=PromptCategory.GENERAL.value, index=True)
    version = Column(Integer, nullable=False, default=1)
    system_prompt = Column(Text, nullable=True)
    user_prompt_template = Column(Text, nullable=False)
    input_variables = Column(JSON, nullable=False, default=list)  # e.g. ["product_name", "tone"]
    expected_output_schema = Column(String(100), nullable=True)  # schema model name if structured
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    logs = relationship(
        "AIGenerationLog",
        back_populates="prompt_template",
        cascade="all, delete-orphan",
    )


class AIGenerationLog(Base):
    __tablename__ = "ai_generation_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_name = Column(String(50), nullable=False, index=True)
    model_name = Column(String(100), nullable=False)
    prompt_template_id = Column(
        String(36),
        ForeignKey("prompt_templates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    prompt_slug = Column(String(100), nullable=True, index=True)
    prompt_version = Column(Integer, nullable=True)
    input_prompt_sanitized = Column(Text, nullable=False)
    system_prompt_sanitized = Column(Text, nullable=True)
    raw_output = Column(Text, nullable=True)
    parsed_json = Column(JSON, nullable=True)
    status = Column(String(50), nullable=False, default=AILogStatus.SUCCESS.value, index=True)
    error_message = Column(Text, nullable=True)
    prompt_tokens = Column(Integer, nullable=False, default=0)
    completion_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    estimated_cost_usd = Column(Float, nullable=False, default=0.0)
    latency_ms = Column(Integer, nullable=False, default=0)
    retry_count = Column(Integer, nullable=False, default=0)
    created_by_user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    prompt_template = relationship("PromptTemplate", back_populates="logs")

    __table_args__ = (
        Index("idx_ai_logs_provider_created", "provider_name", "created_at"),
        Index("idx_ai_logs_status_created", "status", "created_at"),
    )
