from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CustomerAddressBase(BaseModel):
    receiver_name: str
    phone: str
    address_line: str
    district: Optional[str] = None
    city: str = "Hồ Chí Minh"
    is_default: bool = False


class CustomerAddressResponse(CustomerAddressBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    customer_id: str
    created_at: datetime


class CustomerBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=9, max_length=20)
    email: Optional[str] = Field(None, max_length=120)
    date_of_birth: Optional[datetime] = None
    default_address: Optional[str] = None
    source: str = "ONLINE"
    tags: Optional[List[str]] = Field(default_factory=list)
    notes: Optional[str] = None
    consent_marketing: bool = True


class CustomerCreateInput(CustomerBase):
    pass


class CustomerUpdateInput(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[str] = Field(None, max_length=120)
    date_of_birth: Optional[datetime] = None
    default_address: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    consent_marketing: Optional[bool] = None
    segment: Optional[str] = None


class CustomerListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    phone: str
    email: Optional[str] = None
    default_address: Optional[str] = None
    source: str
    segment: str
    order_count: int
    total_spent: float
    average_order_value: float
    loyalty_points: int
    tags: List[str] = Field(default_factory=list)
    last_order_at: Optional[datetime] = None
    created_at: datetime


class CustomerListResponse(BaseModel):
    items: List[CustomerListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class LoyaltyTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    order_id: Optional[str] = None
    transaction_type: str
    points: int
    balance_after: int
    reason: str
    created_by_user_id: Optional[str] = None
    created_at: datetime


class LoyaltyAdjustRequest(BaseModel):
    points: int = Field(..., description="Số điểm cộng (+) hoặc trừ (-)")
    reason: str = Field(..., min_length=3, max_length=255, description="Lý do điều chỉnh điểm")


class CustomerOrderSummary(BaseModel):
    id: str
    order_number: str
    status: str
    payment_status: str
    total_amount: float
    items_count: int
    source: str
    created_at: datetime


class FavoriteProductItem(BaseModel):
    product_name: str
    quantity_bought: int
    total_spent: float


class Customer360Response(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    phone: str
    email: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    default_address: Optional[str] = None
    source: str
    segment: str
    order_count: int
    total_spent: float
    average_order_value: float
    loyalty_points: int
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    consent_marketing: bool
    first_order_at: Optional[datetime] = None
    last_order_at: Optional[datetime] = None
    days_since_last_order: Optional[int] = None
    most_used_channel: str
    favorite_products: List[FavoriteProductItem] = Field(default_factory=list)
    recent_orders: List[CustomerOrderSummary] = Field(default_factory=list)
    recent_loyalty_transactions: List[LoyaltyTransactionResponse] = Field(default_factory=list)
    created_at: datetime


class CustomerOverviewStats(BaseModel):
    total_customers: int
    vip_customers: int
    new_customers_this_month: int
    at_risk_customers: int
    total_loyalty_points_circulating: int
    average_ltv: float
