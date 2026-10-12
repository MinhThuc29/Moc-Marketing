from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.promotion import FreeGiftItem


class AddToCartRequest(BaseModel):
    product_id: str = Field(..., description="ID sản phẩm cần thêm")
    quantity: int = Field(1, ge=1, le=100, description="Số lượng đặt")
    note: Optional[str] = Field(None, max_length=255, description="Ghi chú đặc biệt (ví dụ: ít ngọt, không đá)")


class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(..., ge=1, le=100, description="Số lượng cập nhật")
    note: Optional[str] = Field(None, max_length=255, description="Ghi chú đặc biệt")


class ApplyCouponRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=50, description="Mã khuyến mãi / voucher")


class CartItemResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    product_sku: str
    product_slug: str
    product_unit: str
    thumbnail: Optional[str] = None
    unit_price: float
    original_price: float
    quantity: int
    line_total: float
    note: Optional[str] = None
    is_available: bool = True
    stock_available: int = 999

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    cart_token: str
    items: List[CartItemResponse]
    total_items: int
    subtotal: float
    discount_amount: float
    shipping_fee: float
    shipping_discount: float
    final_total: float
    applied_promo_code: Optional[str] = None
    applied_promo_title: Optional[str] = None
    promo_message: Optional[str] = None
    free_gifts: List[FreeGiftItem] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class CartValidationIssue(BaseModel):
    product_id: str
    product_name: str
    issue_type: str  # "INACTIVE", "OUT_OF_STOCK", "PRICE_CHANGED", "PROMO_INVALID"
    message: str


class CartValidationResponse(BaseModel):
    is_valid: bool
    issues: List[CartValidationIssue] = Field(default_factory=list)
    cart: CartResponse
