from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class AIProviderHealthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str = Field(..., description="ONLINE, DEGRADED, OFFLINE")
    provider: str
    model: str
    latency_ms: int
    is_mock: bool
    message: str


class AIProviderInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    type: str
    default_model: str
    is_active: bool
    description: str


class PromptTemplateCreate(BaseModel):
    slug: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=2, max_length=200)
    category: str = Field(default="GENERAL")
    system_prompt: Optional[str] = None
    user_prompt_template: str = Field(..., min_length=5)
    input_variables: List[str] = Field(default_factory=list)
    expected_output_schema: Optional[str] = None
    is_active: bool = True


class PromptTemplateUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    input_variables: Optional[List[str]] = None
    expected_output_schema: Optional[str] = None
    is_active: Optional[bool] = None
    bump_version: bool = True


class PromptTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    name: str
    category: str
    version: int
    system_prompt: Optional[str] = None
    user_prompt_template: str
    input_variables: List[str] = Field(default_factory=list)
    expected_output_schema: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PromptTemplateListResponse(BaseModel):
    total: int
    items: List[PromptTemplateResponse]


class AITestGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    system_prompt: Optional[str] = None
    template_slug: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=10, le=8000)
    expect_json: bool = False
    simulate_behavior: Optional[str] = None  # None, "timeout", "malformed_json", "fail", "retry_success"


class AITestGenerateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    success: bool
    text_output: Optional[str] = None
    json_output: Optional[Dict[str, Any]] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    latency_ms: int = 0
    provider: str
    model: str
    log_id: Optional[str] = None
    sanitized_input: str
    error_message: Optional[str] = None


class AIGenerationLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    provider_name: str
    model_name: str
    prompt_template_id: Optional[str] = None
    prompt_slug: Optional[str] = None
    prompt_version: Optional[int] = None
    input_prompt_sanitized: str
    system_prompt_sanitized: Optional[str] = None
    raw_output: Optional[str] = None
    parsed_json: Optional[Dict[str, Any]] = None
    status: str
    error_message: Optional[str] = None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    latency_ms: int
    retry_count: int
    created_by_user_id: Optional[str] = None
    created_at: datetime


class AIGenerationLogListResponse(BaseModel):
    total: int
    items: List[AIGenerationLogResponse]
