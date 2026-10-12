from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class TrackingEventCreate(BaseModel):
    event_name: str = Field(..., description="Tên sự kiện: page_view, product_view, add_to_cart, purchase, etc.")
    anonymous_id: str = Field(..., description="ID ẩn danh lưu trong cookie trình duyệt")
    session_id: str = Field(..., description="ID phiên truy cập web")
    user_id: Optional[str] = None
    customer_id: Optional[str] = None
    page_url: Optional[str] = None
    referrer: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    utm_term: Optional[str] = None
    channel: Optional[str] = None
    product_id: Optional[str] = None
    order_id: Optional[str] = None
    campaign_id: Optional[str] = None
    content_id: Optional[str] = None
    event_metadata: Dict[str, Any] = Field(default_factory=dict)


class TrackingBatchCreate(BaseModel):
    events: List[TrackingEventCreate]


class TrackingEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_name: str
    anonymous_id: str
    session_id: str
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    channel: Optional[str] = None
    product_id: Optional[str] = None
    order_id: Optional[str] = None
    campaign_id: Optional[str] = None
    content_id: Optional[str] = None
    created_at: datetime


class ConversionAttributionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order_id: str
    order_number: str
    attribution_model: str
    confidence: str
    first_touch_source: Optional[str] = None
    last_touch_source: Optional[str] = None
    campaign_id: Optional[str] = None
    campaign_code: Optional[str] = None
    content_id: Optional[str] = None
    touchpoints_count: int
    order_revenue: float
    attributed_revenue: float
    attribution_weight: float
    touchpoint_details: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime


class AnalyticsKPIOverview(BaseModel):
    gross_revenue: float
    net_revenue: float
    total_orders: int
    aov: float
    attributed_revenue: float
    attribution_rate: float
    marketing_spend: float
    roas: float
    mer: float
    new_customers: int
    returning_customers: int
    cac: float
    ltv: float
    ltv_to_cac_ratio: float


class ChannelAnalyticsItem(BaseModel):
    channel: str
    channel_name: str
    orders_count: int
    gross_sales: float
    platform_fees: float
    merchant_discounts: float
    net_revenue: float
    net_margin_percentage: float
    aov: float
    share_of_sales: float


class CampaignAttributionComparison(BaseModel):
    campaign_id: str
    campaign_name: str
    campaign_code: str
    channel: str
    spend: float
    first_touch_revenue: float
    first_touch_roas: float
    last_touch_revenue: float
    last_touch_roas: float
    linear_revenue: float
    linear_roas: float
    confidence: str
    orders_count: int
    new_customers_acquired: int


class FunnelStepItem(BaseModel):
    step_key: str
    step_name: str
    count: int
    conversion_from_top: float
    drop_off_rate: float


class AIAnalyticsInsightItem(BaseModel):
    type: str  # SUCCESS, WARNING, RECOMMENDATION, INFO
    title: str
    description: str
    metric_highlight: Optional[str] = None
    suggested_action: Optional[str] = None


class AnalyticsDashboardResponse(BaseModel):
    period: str
    start_date: str
    end_date: str
    kpis: AnalyticsKPIOverview
    channel_breakdown: List[ChannelAnalyticsItem]
    campaign_attributions: List[CampaignAttributionComparison]
    funnel: List[FunnelStepItem]
    ai_insights: List[AIAnalyticsInsightItem]
