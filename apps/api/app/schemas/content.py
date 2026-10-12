from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class ContentCreateInput(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    content_type: str = "FACEBOOK_POST"
    channel: str = "FACEBOOK"
    brand_tone: str = "FRESH_ENERGETIC"
    hook: Optional[str] = Field(None, max_length=500)
    body: str = Field(..., min_length=10)
    cta: Optional[str] = Field(None, max_length=500)
    hashtags: Optional[List[str]] = Field(default_factory=list)
    media_asset_ids: Optional[List[str]] = Field(default_factory=list)
    campaign_id: Optional[str] = None
    product_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None


class ContentUpdateInput(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    content_type: Optional[str] = None
    channel: Optional[str] = None
    brand_tone: Optional[str] = None
    hook: Optional[str] = None
    body: Optional[str] = None
    cta: Optional[str] = None
    hashtags: Optional[List[str]] = None
    media_asset_ids: Optional[List[str]] = None
    campaign_id: Optional[str] = None
    product_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None


class AIGenerateRequest(BaseModel):
    product_id: Optional[str] = None
    campaign_id: Optional[str] = None
    channel: str = "FACEBOOK"
    content_type: str = "FACEBOOK_POST"
    brand_tone: str = "FRESH_ENERGETIC"
    custom_instruction: Optional[str] = Field(None, max_length=1000)
    num_variants: int = Field(2, ge=1, le=3)


class AIGeneratedVariant(BaseModel):
    title: str
    hook: str
    body: str
    cta: str
    hashtags: List[str]
    storyboard_suggestion: Optional[str] = None
    rationale: str


class AIGenerateResponse(BaseModel):
    variants: List[AIGeneratedVariant]
    prompt_used: str
    model_name: str
    product_name: Optional[str] = None
    campaign_name: Optional[str] = None


class ContentScheduleRequest(BaseModel):
    scheduled_at: datetime


class ContentStatusUpdateRequest(BaseModel):
    status: str
    reason: Optional[str] = None


class ContentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    content_type: str
    channel: str
    status: str
    brand_tone: str
    hook: Optional[str] = None
    body_snippet: str
    cta: Optional[str] = None
    hashtags: List[str] = Field(default_factory=list)
    media_asset_ids: List[str] = Field(default_factory=list)
    campaign_id: Optional[str] = None
    campaign_name: Optional[str] = None
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    ai_generated: bool
    ai_model: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    external_post_url: Optional[str] = None
    created_at: datetime


class ContentListResponse(BaseModel):
    items: List[ContentListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class ContentDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    content_type: str
    channel: str
    status: str
    brand_tone: str
    hook: Optional[str] = None
    body: str
    cta: Optional[str] = None
    hashtags: List[str] = Field(default_factory=list)
    media_asset_ids: List[str] = Field(default_factory=list)
    campaign_id: Optional[str] = None
    campaign_name: Optional[str] = None
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    product_price: Optional[float] = None
    ai_generated: bool
    ai_model: Optional[str] = None
    ai_prompt: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    external_post_id: Optional[str] = None
    external_post_url: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int
    metrics: Dict[str, Any] = Field(default_factory=dict)
    created_by_user_id: Optional[str] = None
    created_by_user_name: Optional[str] = None
    approved_by_user_id: Optional[str] = None
    approved_by_user_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ContentCalendarItem(BaseModel):
    id: str
    title: str
    content_type: str
    channel: str
    status: str
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    campaign_name: Optional[str] = None
    product_name: Optional[str] = None


class ContentOverviewStats(BaseModel):
    total_items: int
    published_items: int
    scheduled_items: int
    in_review_items: int
    draft_items: int
    ai_generated_items: int
