from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class MediaAssetResponse(BaseModel):
    id: str
    filename: str
    original_name: str
    mime_type: str
    file_size: int
    url: str
    thumbnail_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    folder: str = "products"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MediaAssetListResponse(BaseModel):
    items: List[MediaAssetResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class MediaAssetUpdate(BaseModel):
    original_name: Optional[str] = None
    tags: Optional[List[str]] = None
    folder: Optional[str] = None
