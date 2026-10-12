from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class StorefrontCategory(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    description: Optional[str] = None
    sort_order: int = 0
    product_count: int = 0


class StorefrontProduct(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    sku: str
    slug: str
    name: str
    short_description: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    category_slug: Optional[str] = None
    base_price: float
    sale_price: Optional[float] = None
    discount_percent: Optional[int] = None
    unit: str = "phần"
    status: str = "ACTIVE"
    featured: bool = False
    tags: List[str] = []
    ingredients: Optional[str] = None
    allergens: Optional[str] = None
    nutrition_text: Optional[str] = None
    preparation_note: Optional[str] = None
    storage_note: Optional[str] = None
    shelf_life: Optional[str] = None
    thumbnail: Optional[str] = None
    media: List[str] = []


class StorefrontProductDetail(StorefrontProduct):
    related_products: List[StorefrontProduct] = []


class StorefrontPromotionItem(BaseModel):
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
    stackable: bool = False


class StorefrontHomeResponse(BaseModel):
    banners: List[StorefrontPromotionItem]
    categories: List[StorefrontCategory]
    featured_products: List[StorefrontProduct]
    category_sections: Dict[str, List[StorefrontProduct]]
    active_vouchers: List[StorefrontPromotionItem]


class StorefrontProductListResponse(BaseModel):
    items: List[StorefrontProduct]
    total: int
    page: int
    page_size: int
    total_pages: int
