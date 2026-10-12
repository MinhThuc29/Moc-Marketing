from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CampaignChannelInput(BaseModel):
    channel: str = Field(..., description="Kênh: FACEBOOK, ZALO, TIKTOK, INSTAGRAM, SMS, EMAIL, WEBSITE_BANNER")
    channel_budget: float = Field(0.0, ge=0)
    target_metric: Optional[str] = Field(None, description="Chỉ số kỳ vọng: 10k views, 50 orders...")
    notes: Optional[str] = None


class CampaignChannelResponse(CampaignChannelInput):
    model_config = ConfigDict(from_attributes=True)
    id: str
    campaign_id: str
    channel_spend: float = 0.0
    status: str = "ACTIVE"
    created_at: datetime


class CampaignProductInput(BaseModel):
    product_id: str
    is_hero_product: bool = False
    special_price: Optional[float] = None


class CampaignProductResponse(CampaignProductInput):
    model_config = ConfigDict(from_attributes=True)
    id: str
    campaign_id: str
    product_name: str
    product_price: float
    created_at: datetime


class CampaignCreateInput(BaseModel):
    name: str = Field(..., min_length=3, max_length=150)
    code: str = Field(..., min_length=2, max_length=50)
    objective: str = "CONVERSION"
    start_at: datetime
    end_at: datetime
    budget: float = Field(0.0, ge=0)
    target_audience: Optional[List[str]] = Field(default_factory=list)
    promotion_id: Optional[str] = None
    landing_page: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    notes: Optional[str] = None
    channels: Optional[List[CampaignChannelInput]] = Field(default_factory=list)
    products: Optional[List[CampaignProductInput]] = Field(default_factory=list)


class CampaignUpdateInput(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=150)
    objective: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    budget: Optional[float] = Field(None, ge=0)
    target_audience: Optional[List[str]] = None
    promotion_id: Optional[str] = None
    landing_page: Optional[str] = None
    notes: Optional[str] = None
    channels: Optional[List[CampaignChannelInput]] = None
    products: Optional[List[CampaignProductInput]] = None


class CampaignStatusUpdateRequest(BaseModel):
    status: str
    reason: Optional[str] = None


class CampaignListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    code: str
    objective: str
    status: str
    start_at: datetime
    end_at: datetime
    budget: float
    actual_spend: float
    revenue_attributed: float
    roi_percentage: float
    target_audience: List[str] = Field(default_factory=list)
    channels_count: int
    products_count: int
    created_at: datetime


class CampaignListResponse(BaseModel):
    items: List[CampaignListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class CampaignDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    code: str
    objective: str
    status: str
    start_at: datetime
    end_at: datetime
    budget: float
    actual_spend: float
    revenue_attributed: float
    roi_percentage: float
    target_audience: List[str] = Field(default_factory=list)
    promotion_id: Optional[str] = None
    promotion_name: Optional[str] = None
    landing_page: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    notes: Optional[str] = None
    created_by_user_id: Optional[str] = None
    created_by_user_name: Optional[str] = None
    approved_by_user_id: Optional[str] = None
    approved_by_user_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    channels: List[CampaignChannelResponse] = Field(default_factory=list)
    products: List[CampaignProductResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class CampaignOverviewStats(BaseModel):
    active_campaigns: int
    ready_for_review_campaigns: int
    total_budget_approved: float
    total_revenue_attributed: float
    average_roi_percentage: float
