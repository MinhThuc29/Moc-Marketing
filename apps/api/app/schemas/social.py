from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class SocialConnectionCreate(BaseModel):
    platform: str = Field(..., description="Platform: FACEBOOK, INSTAGRAM, TIKTOK, ZALO_OA, WEBSITE_BLOG")
    account_name: str = Field(..., description="Tên trang / tài khoản hiển thị")
    account_id: str = Field(..., description="ID định danh tài khoản mạng xã hội")
    app_id: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    is_mock: bool = Field(default=True, description="Chế độ mô phỏng Sandbox / Mock")
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SocialConnectionUpdate(BaseModel):
    account_name: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    is_connected: Optional[bool] = None
    status: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class SocialConnectionResponse(BaseModel):
    id: str
    platform: str
    account_name: str
    account_id: str
    app_id: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    is_connected: bool
    status: str
    is_mock: bool
    metadata_json: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PostMetricResponse(BaseModel):
    id: str
    published_post_id: str
    recorded_at: datetime
    impressions: int
    reach: int
    likes: int
    comments: int
    shares: int
    clicks: int
    conversions: int
    raw_data_json: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PublishedPostResponse(BaseModel):
    id: str
    content_id: str
    connection_id: Optional[str] = None
    channel: str
    external_post_id: Optional[str] = None
    external_post_url: Optional[str] = None
    publish_status: str
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    retry_count: int
    max_retries: int
    next_retry_at: Optional[datetime] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    payload_snapshot: Dict[str, Any]
    latest_metric: Optional[PostMetricResponse] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PublishedPostListResponse(BaseModel):
    items: List[PublishedPostResponse]
    total: int


class PublishNowRequest(BaseModel):
    connection_id: Optional[str] = None
    force_mock: Optional[bool] = True


class PublishNowResponse(BaseModel):
    success: bool
    message: str
    published_post: PublishedPostResponse


class WorkerBatchResult(BaseModel):
    processed: int
    published: int
    retried: int
    failed: int
    details: List[Dict[str, Any]]


class ConnectionTestResult(BaseModel):
    is_valid: bool
    status: str
    message: str
    account_info: Optional[Dict[str, Any]] = None


class TokenRefreshResult(BaseModel):
    success: bool
    message: str
    expires_at: Optional[datetime] = None
