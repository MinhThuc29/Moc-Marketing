import enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


class OrderStatusEnum(str, enum.Enum):
    NEW = "NEW"
    CONFIRMED = "CONFIRMED"
    PREPARING = "PREPARING"
    READY = "READY"
    SHIPPING = "SHIPPING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class PaymentMethodEnum(str, enum.Enum):
    COD = "COD"
    BANK_TRANSFER = "BANK_TRANSFER"


class PaymentStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class OrderSourceEnum(str, enum.Enum):
    STOREFRONT_WEB = "STOREFRONT_WEB"
    ADMIN = "ADMIN"
    PHONE = "PHONE"
    WALK_IN = "WALK_IN"
    GRAB = "GRAB"
    SHOPEEFOOD = "SHOPEEFOOD"
    MANUAL = "MANUAL"


class OrderStatusUpdateRequest(BaseModel):
    new_status: OrderStatusEnum = Field(..., description="Trạng thái đơn hàng mới")
    reason: Optional[str] = Field(None, max_length=500, description="Lý do hoặc ghi chú chuyển trạng thái")


class OrderPaymentStatusUpdateRequest(BaseModel):
    payment_status: PaymentStatusEnum = Field(..., description="Trạng thái thanh toán mới")
    note: Optional[str] = Field(None, max_length=500, description="Ghi chú xác nhận thanh toán")


class OrderInternalNoteUpdateRequest(BaseModel):
    internal_note: str = Field(..., max_length=1000, description="Ghi chú nội bộ cho đơn hàng")


class OrderItemInput(BaseModel):
    product_id: str
    quantity: int = Field(1, ge=1, le=100)
    note: Optional[str] = None


class ManualOrderCreateRequest(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=255)
    customer_phone: str = Field(..., min_length=9, max_length=20)
    customer_email: Optional[str] = None
    delivery_address: str = Field(..., min_length=5, max_length=500)
    customer_note: Optional[str] = None
    internal_note: Optional[str] = None
    source: OrderSourceEnum = OrderSourceEnum.WALK_IN
    payment_method: PaymentMethodEnum = PaymentMethodEnum.COD
    payment_status: PaymentStatusEnum = PaymentStatusEnum.PENDING
    items: List[OrderItemInput] = Field(..., min_length=1)
    shipping_fee: float = Field(0.0, ge=0)
    applied_promo_code: Optional[str] = None


class OrderItemResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    product_sku: str
    product_unit: str
    thumbnail: Optional[str] = None
    unit_price: float
    quantity: int
    total_price: float
    note: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OrderStatusHistoryResponse(BaseModel):
    id: str
    order_id: str
    previous_status: Optional[str] = None
    new_status: str
    changed_by_user_id: Optional[str] = None
    changed_by_user_name: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminOrderListItemResponse(BaseModel):
    id: str
    order_number: str
    customer_name: str
    customer_phone: str
    delivery_address: str
    source: str
    status: str
    payment_method: str
    payment_status: str
    total_amount: float
    items_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminOrderListResponse(BaseModel):
    items: List[AdminOrderListItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AdminOrderDetailResponse(BaseModel):
    id: str
    order_number: str
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    delivery_address: str
    customer_note: Optional[str] = None
    internal_note: Optional[str] = None
    source: str
    status: str
    payment_method: str
    payment_status: str
    subtotal: float
    discount_amount: float
    shipping_fee: float
    shipping_discount: float
    total_amount: float
    applied_promo_code: Optional[str] = None
    user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]
    status_history: List[OrderStatusHistoryResponse]

    model_config = ConfigDict(from_attributes=True)


class OrderOverviewStatsResponse(BaseModel):
    total_orders: int
    new_orders: int
    in_progress_orders: int
    completed_today: int
    cancelled_orders: int
    revenue_today: float


class OrderTrackingRequest(BaseModel):
    order_number: str = Field(..., min_length=5, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)


class OrderTrackingResponse(BaseModel):
    order_number: str
    status: str
    customer_name: str
    customer_phone: str
    delivery_address: str
    items: List[OrderItemResponse]
    total_amount: float
    payment_method: str
    payment_status: str
    created_at: datetime
    status_history: List[OrderStatusHistoryResponse]

    model_config = ConfigDict(from_attributes=True)
