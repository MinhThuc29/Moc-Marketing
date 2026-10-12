import enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator


class PaymentMethodEnum(str, enum.Enum):
    COD = "COD"
    BANK_TRANSFER = "BANK_TRANSFER"


class CheckoutRequest(BaseModel):
    cart_token: str = Field(..., min_length=10, max_length=64, description="Token giỏ hàng")
    customer_name: str = Field(..., min_length=2, max_length=255, description="Họ và tên người nhận")
    customer_phone: str = Field(..., min_length=9, max_length=20, description="Số điện thoại liên hệ")
    customer_email: Optional[str] = Field(None, max_length=255, description="Email nhận thông tin đơn hàng")
    delivery_address: str = Field(..., min_length=5, max_length=500, description="Địa chỉ giao hàng chi tiết")
    customer_note: Optional[str] = Field(None, max_length=500, description="Ghi chú giao hàng")
    payment_method: PaymentMethodEnum = Field(default=PaymentMethodEnum.COD, description="Phương thức thanh toán")
    terms_accepted: bool = Field(..., description="Xác nhận đồng ý điều khoản mua hàng")
    idempotency_key: Optional[str] = Field(None, max_length=100, description="Khóa chống trùng đơn hàng")

    @field_validator("terms_accepted")
    @classmethod
    def validate_terms(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Quý khách vui lòng đồng ý với điều khoản mua hàng trước khi đặt hàng.")
        return v

    @field_validator("customer_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        clean = v.strip().replace(" ", "").replace(".", "").replace("-", "")
        if not clean.isdigit() and not (clean.startswith("+") and clean[1:].isdigit()):
            raise ValueError("Số điện thoại không hợp lệ. Vui lòng chỉ nhập số.")
        if len(clean) < 9 or len(clean) > 13:
            raise ValueError("Số điện thoại phải có từ 9 đến 12 chữ số.")
        return clean


class BankTransferInstruction(BaseModel):
    bank_name: str = "Ngân hàng TMCP Quân Đội (MBBank)"
    bank_code: str = "MB"
    account_number: str = "0901234567"
    account_holder: str = "MOC HEALTHY FRESH FOOD"
    transfer_content: str
    amount: float
    qr_code_url: str


class OrderItemSnapshotResponse(BaseModel):
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


class CheckoutResponse(BaseModel):
    order_id: str
    order_number: str
    status: str
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    delivery_address: str
    customer_note: Optional[str] = None
    items: List[OrderItemSnapshotResponse]
    subtotal: float
    discount_amount: float
    shipping_fee: float
    shipping_discount: float
    total_amount: float
    payment_method: str
    payment_status: str
    applied_promo_code: Optional[str] = None
    bank_transfer_instruction: Optional[BankTransferInstruction] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
