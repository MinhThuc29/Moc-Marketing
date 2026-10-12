import enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, model_validator


class PromotionTypeEnum(str, enum.Enum):
    PERCENT_DISCOUNT = "PERCENT_DISCOUNT"
    FIXED_DISCOUNT = "FIXED_DISCOUNT"
    FLASH_SALE = "FLASH_SALE"
    BUY_X_GET_Y = "BUY_X_GET_Y"
    COMBO = "COMBO"
    FREE_SHIPPING = "FREE_SHIPPING"
    VOUCHER = "VOUCHER"


class PromotionStatusEnum(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    EXPIRED = "EXPIRED"


class ProductScopeEnum(str, enum.Enum):
    ALL = "ALL"
    SPECIFIC_PRODUCTS = "SPECIFIC_PRODUCTS"
    SPECIFIC_CATEGORIES = "SPECIFIC_CATEGORIES"


class CustomerScopeEnum(str, enum.Enum):
    ALL = "ALL"
    NEW_CUSTOMER = "NEW_CUSTOMER"
    VIP = "VIP"


class PromotionCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255, description="Tên chương trình khuyến mãi")
    code: Optional[str] = Field(None, max_length=50, description="Mã voucher (tự động viết hoa nếu có)")
    description: Optional[str] = None
    type: PromotionTypeEnum
    value: float = Field(..., gt=0, description="Giá trị giảm (% hoặc VND)")
    min_order_value: Optional[float] = Field(None, ge=0, description="Giá trị đơn hàng tối thiểu")
    max_discount: Optional[float] = Field(None, ge=0, description="Mức giảm tối đa cho % hoặc ship")
    start_at: datetime = Field(..., description="Thời gian bắt đầu áp dụng")
    end_at: datetime = Field(..., description="Thời gian kết thúc chương trình")
    product_scope: ProductScopeEnum = ProductScopeEnum.ALL
    applicable_product_ids: List[str] = Field(default_factory=list)
    applicable_category_ids: List[str] = Field(default_factory=list)
    buy_x_get_y_config: Optional[Dict[str, Any]] = None
    combo_config: Optional[Dict[str, Any]] = None
    customer_scope: CustomerScopeEnum = CustomerScopeEnum.ALL
    usage_limit: Optional[int] = Field(None, ge=1, description="Tổng lượt dùng toàn hệ thống")
    usage_per_customer: Optional[int] = Field(1, ge=1, description="Số lượt dùng tối đa / khách")
    stackable: bool = Field(False, description="Cho phép gộp với khuyến mãi khác hay không")
    status: PromotionStatusEnum = PromotionStatusEnum.ACTIVE

    @model_validator(mode="after")
    def validate_dates_and_values(self):
        if self.end_at <= self.start_at:
            raise ValueError("Thời gian kết thúc (end_at) phải lớn hơn thời gian bắt đầu (start_at).")
        if self.type in [PromotionTypeEnum.PERCENT_DISCOUNT, PromotionTypeEnum.FLASH_SALE] and self.value > 100:
            raise ValueError("Khuyến mãi theo phần trăm không được vượt quá 100%.")
        if self.code:
            self.code = self.code.strip().upper()
        return self


class PromotionUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    type: Optional[PromotionTypeEnum] = None
    value: Optional[float] = Field(None, gt=0)
    min_order_value: Optional[float] = None
    max_discount: Optional[float] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    product_scope: Optional[ProductScopeEnum] = None
    applicable_product_ids: Optional[List[str]] = None
    applicable_category_ids: Optional[List[str]] = None
    buy_x_get_y_config: Optional[Dict[str, Any]] = None
    combo_config: Optional[Dict[str, Any]] = None
    customer_scope: Optional[CustomerScopeEnum] = None
    usage_limit: Optional[int] = None
    usage_per_customer: Optional[int] = None
    stackable: Optional[bool] = None
    status: Optional[PromotionStatusEnum] = None


class PromotionStatusUpdateRequest(BaseModel):
    status: PromotionStatusEnum


class PromotionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    code: Optional[str] = None
    description: Optional[str] = None
    type: str
    value: float
    min_order_value: Optional[float] = None
    max_discount: Optional[float] = None
    start_at: datetime
    end_at: datetime
    product_scope: str
    applicable_product_ids: List[str] = []
    applicable_category_ids: List[str] = []
    buy_x_get_y_config: Optional[Dict[str, Any]] = None
    combo_config: Optional[Dict[str, Any]] = None
    customer_scope: str
    usage_limit: Optional[int] = None
    usage_count: int
    usage_per_customer: Optional[int] = 1
    stackable: bool
    status: str
    created_at: datetime
    updated_at: datetime
    is_valid_now: bool = False


class PromotionListResponse(BaseModel):
    items: List[PromotionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CartItemInput(BaseModel):
    product_id: str
    quantity: int = Field(..., ge=1, description="Số lượng đặt")
    unit_price: float = Field(..., ge=0, description="Giá niêm yết hiện tại")
    category_id: Optional[str] = None
    name: Optional[str] = None


class CalculationRequest(BaseModel):
    items: List[CartItemInput] = Field(..., min_length=1, description="Danh sách sản phẩm trong giỏ")
    promo_code: Optional[str] = Field(None, description="Mã voucher nhập tay (nếu có)")
    shipping_fee: float = Field(0.0, ge=0, description="Phí vận chuyển")
    is_new_customer: bool = Field(False, description="Cờ nhận diện khách hàng mới")
    as_of: Optional[datetime] = Field(None, description="Thời điểm tính toán (hỗ trợ test deterministic)")


class AppliedPromotionItem(BaseModel):
    promotion_id: str
    title: str
    code: Optional[str] = None
    type: str
    discount_amount: float
    description: str


class FreeGiftItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    reason: str


class CalculationResponse(BaseModel):
    subtotal: float
    discount_amount: float
    shipping_fee: float
    shipping_discount: float
    final_total: float
    applied_promotions: List[AppliedPromotionItem]
    free_items: List[FreeGiftItem]
    rejection_reasons: List[str]
    is_code_valid: bool
