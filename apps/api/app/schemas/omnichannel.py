from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class MarketplaceImportPreviewItem(BaseModel):
    row_index: int
    external_order_id: str
    channel: str
    customer_name: str
    customer_phone: str
    ordered_at: str
    gross_amount: float
    merchant_discount: float
    platform_fee: float
    net_amount: float
    items_count: int
    is_duplicate: bool
    error: Optional[str] = None


class MarketplaceImportPreviewResponse(BaseModel):
    channel: str
    filename: str
    total_rows: int
    valid_rows: int
    duplicate_rows: int
    error_rows: int
    gross_amount_total: float
    platform_fee_total: float
    merchant_discount_total: float
    net_settlement_total: float
    preview_items: List[MarketplaceImportPreviewItem]


class MarketplaceImportExecuteRequest(BaseModel):
    channel: str
    filename: str
    raw_content: str
    skip_duplicates: bool = True


class MarketplaceImportResponse(BaseModel):
    id: str
    channel: str
    filename: str
    file_format: str
    status: str
    total_rows: int
    imported_rows: int
    duplicate_rows: int
    rejected_rows: int
    gross_amount_total: float
    platform_fee_total: float
    merchant_discount_total: float
    net_settlement_total: float
    started_at: str
    completed_at: Optional[str] = None


class SettlementCreateRequest(BaseModel):
    channel: str
    external_settlement_id: Optional[str] = None
    period_start: datetime
    period_end: datetime
    gross_amount: float = Field(..., ge=0)
    platform_fee: float = Field(..., ge=0)
    merchant_discount: float = Field(default=0.0, ge=0)
    other_fee: float = Field(default=0.0, ge=0)
    notes: Optional[str] = None


class SettlementOrderResponse(BaseModel):
    id: str
    order_id: str
    order_number: str
    external_order_id: Optional[str] = None
    allocated_amount: float
    platform_fee: float
    merchant_discount: float
    status: str
    matched_at: str


class SettlementResponse(BaseModel):
    id: str
    channel: str
    external_settlement_id: Optional[str] = None
    period_start: str
    period_end: str
    gross_amount: float
    platform_fee: float
    merchant_discount: float
    other_fee: float
    net_amount: float
    status: str
    paid_at: Optional[str] = None
    notes: Optional[str] = None
    matched_orders_count: int = 0
    matched_amount: float = 0.0
    discrepancy_amount: float = 0.0
    created_at: str


class SettlementDetailResponse(SettlementResponse):
    orders: List[SettlementOrderResponse] = []


class SettlementReconcileResult(BaseModel):
    settlement_id: str
    status: str
    total_orders_in_period: int
    matched_orders: int
    unmatched_orders: int
    total_settlement_net: float
    total_orders_net: float
    discrepancy: float


class ChannelPnLSummary(BaseModel):
    channel: str
    order_count: int
    gross_revenue: float
    merchant_discount: float
    platform_fees: float
    net_settlement: float
    average_order_value: float
    net_revenue_per_order: float
    net_margin_percentage: float


class OmnichannelPnLResponse(BaseModel):
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    channels: List[ChannelPnLSummary]
    totals: ChannelPnLSummary
