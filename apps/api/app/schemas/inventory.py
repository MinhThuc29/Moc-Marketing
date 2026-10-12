import enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class BatchStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DEPLETED = "DEPLETED"
    EXPIRED = "EXPIRED"
    QUARANTINED = "QUARANTINED"
    DISCARDED = "DISCARDED"


class MovementTypeEnum(str, enum.Enum):
    PURCHASE_IN = "PURCHASE_IN"
    SALE_OUT = "SALE_OUT"
    WASTE_OUT = "WASTE_OUT"
    ADJUSTMENT_IN = "ADJUSTMENT_IN"
    ADJUSTMENT_OUT = "ADJUSTMENT_OUT"
    RETURN_IN = "RETURN_IN"


class BatchCreateRequest(BaseModel):
    product_id: str
    batch_code: Optional[str] = None
    quantity_received: int = Field(gt=0, description="Số lượng nhập kho ban đầu")
    cost_per_unit: Optional[float] = Field(default=None, ge=0, description="Giá vốn trên một đơn vị")
    supplier: Optional[str] = Field(default=None, max_length=255)
    received_at: Optional[datetime] = None
    expiry_at: datetime = Field(..., description="Thời hạn sử dụng của lô hàng")
    note: Optional[str] = None


class BatchUpdateRequest(BaseModel):
    status: Optional[BatchStatusEnum] = None
    note: Optional[str] = None
    supplier: Optional[str] = None


class AdjustmentRequest(BaseModel):
    batch_id: str
    movement_type: MovementTypeEnum = Field(..., description="ADJUSTMENT_IN, ADJUSTMENT_OUT, WASTE_OUT, RETURN_IN")
    quantity: int = Field(gt=0, description="Số lượng điều chỉnh/xuất hủy")
    reason: str = Field(min_length=3, max_length=255, description="Lý do điều chỉnh (bắt buộc)")
    note: Optional[str] = None
    reference_id: Optional[str] = None


class FefoAllocationRequest(BaseModel):
    product_id: str
    quantity: int = Field(gt=0, description="Số lượng cần xuất kho theo thuật toán FEFO")
    reference_id: Optional[str] = Field(default=None, description="Mã tham chiếu (vd: mã đơn hàng ORDER-123)")
    note: Optional[str] = None


class InventoryMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    batch_id: str
    product_id: str
    movement_type: str
    quantity: int
    previous_quantity: int
    new_quantity: int
    reference_id: Optional[str] = None
    reason: Optional[str] = None
    note: Optional[str] = None
    created_by_user_id: Optional[str] = None
    created_at: datetime
    batch_code: Optional[str] = None
    product_name: Optional[str] = None
    created_by_user_name: Optional[str] = None


class InventoryBatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    batch_code: str
    quantity_received: int
    quantity_available: int
    cost_per_unit: Optional[float] = None
    supplier: Optional[str] = None
    received_at: datetime
    expiry_at: datetime
    status: str
    note: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    product_unit: Optional[str] = None
    days_to_expiry: Optional[float] = None
    hours_to_expiry: Optional[float] = None
    is_expired: bool = False
    is_critical: bool = False
    is_warning: bool = False


class ProductStockSummaryResponse(BaseModel):
    product_id: str
    product_name: str
    sku: str
    unit: str
    base_price: float
    sale_price: Optional[float] = None
    cost_price: Optional[float] = None
    low_stock_threshold: int
    total_available: int
    batch_count: int
    nearest_expiry: Optional[datetime] = None
    is_low_stock: bool
    has_expiring_batches: bool
    has_expired_batches: bool


class InventoryOverviewResponse(BaseModel):
    total_products: int
    total_batches: int
    total_stock_units: int
    low_stock_products_count: int
    expiring_soon_batches_count: int
    critical_batches_count: int
    expired_batches_count: int
    total_inventory_value: float


class ExpiryAlertItemResponse(BaseModel):
    batch_id: str
    product_id: str
    product_name: str
    product_sku: str
    batch_code: str
    quantity_available: int
    expiry_at: datetime
    days_to_expiry: float
    hours_to_expiry: float
    urgency: str
    estimated_waste_cost: float


class FefoAllocationItemResponse(BaseModel):
    batch_id: str
    batch_code: str
    allocated_quantity: int
    quantity_before: int
    quantity_after: int
    expiry_at: datetime


class FefoAllocationResponse(BaseModel):
    product_id: str
    product_name: str
    requested_quantity: int
    allocated_quantity: int
    is_fully_allocated: bool
    allocations: List[FefoAllocationItemResponse]
