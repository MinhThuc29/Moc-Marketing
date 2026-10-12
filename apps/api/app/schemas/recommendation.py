from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    metric: str = Field(..., description="Tên chỉ số số học thực tế")
    value: Any = Field(..., description="Giá trị dữ liệu truy xuất từ DB")
    comparison: str = Field(..., description="So sánh hoặc ngưỡng cảnh báo")
    source: str = Field(..., description="Bảng nguồn dữ liệu (inventory, orders, crm...)")


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    recommendation_type: str
    status: str
    title: str
    problem_statement: str
    recommended_action: str
    evidence: List[Dict[str, Any]] = []
    target_products: List[Dict[str, Any]] = []
    target_customer_segment: Optional[str] = None
    target_channels: List[str] = []
    suggested_promotion: Optional[Dict[str, Any]] = None
    expected_impact: Optional[Dict[str, Any]] = None
    confidence_score: float = 0.85
    confidence_level: str = "HIGH"
    risks: List[str] = []
    dismiss_reason: Optional[str] = None
    converted_campaign_id: Optional[str] = None
    converted_workflow_id: Optional[str] = None
    applied_at: Optional[datetime] = None
    applied_by_user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class RecommendationListResponse(BaseModel):
    items: List[RecommendationResponse]
    total: int
    page: int = 1
    page_size: int = 20


class RecommendationOverviewStats(BaseModel):
    total_recommendations: int
    pending_count: int
    applied_count: int
    high_confidence_count: int
    active_alerts_count: int
    critical_alerts_count: int


class ConvertCampaignRequest(BaseModel):
    custom_name: Optional[str] = None
    budget: Optional[float] = None


class ConvertWorkflowRequest(BaseModel):
    custom_name: Optional[str] = None


class DismissRecommendationRequest(BaseModel):
    reason: Optional[str] = None


class GenerateRecommendationsRequest(BaseModel):
    force_regenerate: bool = False


class SmartAlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    alert_type: str
    severity: str
    status: str
    title: str
    message: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    metric_data: Dict[str, Any] = {}
    action_url: Optional[str] = None
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class SmartAlertListResponse(BaseModel):
    items: List[SmartAlertResponse]
    total: int


class SmartAlertSummaryResponse(BaseModel):
    critical: int
    warning: int
    info: int
    total_active: int
    recent_alerts: List[SmartAlertResponse]
