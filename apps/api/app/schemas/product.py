from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.product import ProductStatus


# --- Category Schemas ---

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Tên danh mục")
    slug: Optional[str] = Field(None, max_length=255, description="Slug URL thân thiện")
    description: Optional[str] = Field(None, description="Mô tả danh mục")
    sort_order: int = Field(0, description="Thứ tự hiển thị")
    active: bool = Field(True, description="Trạng thái kích hoạt")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    sort_order: Optional[int] = None
    active: Optional[bool] = None


class CategoryResponse(CategoryBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Price Audit Log Schemas ---

class PriceAuditLogResponse(BaseModel):
    id: str
    product_id: str
    old_base_price: Optional[float] = None
    new_base_price: float
    old_sale_price: Optional[float] = None
    new_sale_price: Optional[float] = None
    changed_by_user_id: Optional[str] = None
    change_reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Product Schemas ---

class ProductBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100, description="Mã SKU định danh duy nhất")
    slug: Optional[str] = Field(None, max_length=255, description="Slug đường dẫn sản phẩm")
    name: str = Field(..., min_length=1, max_length=255, description="Tên sản phẩm")
    short_description: Optional[str] = Field(None, max_length=500, description="Mô tả ngắn")
    description: Optional[str] = Field(None, description="Mô tả chi tiết sản phẩm")
    category_id: Optional[str] = Field(None, description="ID danh mục")
    base_price: float = Field(..., ge=0, description="Giá niêm yết gốc (VND)")
    sale_price: Optional[float] = Field(None, ge=0, description="Giá khuyến mãi bán ra (VND)")
    cost_price: Optional[float] = Field(None, ge=0, description="Giá vốn sản phẩm (VND)")
    unit: str = Field("phần", max_length=50, description="Đơn vị tính (ly, hộp, kg...)")
    status: ProductStatus = Field(ProductStatus.DRAFT, description="Trạng thái sản phẩm")
    featured: bool = Field(False, description="Sản phẩm nổi bật / Best seller")
    tags: List[str] = Field(default_factory=list, description="Thẻ phân loại")
    ingredients: Optional[str] = Field(None, description="Thành phần nguyên liệu")
    allergens: Optional[str] = Field(None, description="Cảnh báo dị ứng")
    nutrition_text: Optional[str] = Field(None, description="Thông tin dinh dưỡng / Calories")
    preparation_note: Optional[str] = Field(None, description="Ghi chú chế biến / Pha chế")
    storage_note: Optional[str] = Field(None, description="Hướng dẫn bảo quản")
    shelf_life: Optional[str] = Field(None, max_length=100, description="Hạn sử dụng khuyến nghị")
    thumbnail: Optional[str] = Field(None, max_length=500, description="URL ảnh đại diện")
    media: List[Any] = Field(default_factory=list, description="Danh sách media / hình ảnh chi tiết")
    seo_title: Optional[str] = Field(None, max_length=255, description="Tiêu đề SEO")
    seo_description: Optional[str] = Field(None, description="Mô tả SEO")


class ProductCreate(ProductBase):
    @model_validator(mode="after")
    def validate_prices(self):
        if self.sale_price is not None and self.base_price is not None:
            if self.sale_price > self.base_price:
                raise ValueError("Giá khuyến mãi (sale_price) không được lớn hơn giá gốc (base_price)")
        return self


class ProductUpdate(BaseModel):
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, max_length=255)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    short_description: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    base_price: Optional[float] = Field(None, ge=0)
    sale_price: Optional[float] = Field(None, ge=0)
    cost_price: Optional[float] = Field(None, ge=0)
    unit: Optional[str] = None
    status: Optional[ProductStatus] = None
    featured: Optional[bool] = None
    tags: Optional[List[str]] = None
    ingredients: Optional[str] = None
    allergens: Optional[str] = None
    nutrition_text: Optional[str] = None
    preparation_note: Optional[str] = None
    storage_note: Optional[str] = None
    shelf_life: Optional[str] = None
    thumbnail: Optional[str] = None
    media: Optional[List[Any]] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    change_reason: Optional[str] = Field(None, description="Lý do thay đổi (đặc biệt khi đổi giá)")

    @model_validator(mode="after")
    def validate_prices(self):
        if self.sale_price is not None and self.base_price is not None:
            if self.sale_price > self.base_price:
                raise ValueError("Giá khuyến mãi (sale_price) không được lớn hơn giá gốc (base_price)")
        return self


class ProductResponse(ProductBase):
    id: str
    created_at: datetime
    updated_at: datetime
    category: Optional[CategoryResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ProductDetailResponse(ProductResponse):
    price_logs: List[PriceAuditLogResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class BulkStatusUpdateRequest(BaseModel):
    ids: List[str] = Field(..., min_length=1, description="Danh sách ID sản phẩm cần cập nhật")
    status: ProductStatus = Field(..., description="Trạng thái đích cần chuyển sang")
