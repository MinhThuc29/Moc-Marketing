import io
import os
import uuid
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path
from app.core.config import settings

logger = logging.getLogger(__name__)

# Base directory for local file storage
BASE_UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
BASE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class BaseStorageService(ABC):
    @abstractmethod
    async def upload(
        self,
        file_bytes: bytes,
        original_filename: str,
        content_type: str,
        folder: str = "products",
    ) -> Dict[str, Any]:
        """
        Uploads file bytes and returns metadata dict:
        {
            "filename": str,
            "url": str,
            "thumbnail_url": Optional[str],
            "width": Optional[int],
            "height": Optional[int],
            "file_size": int,
        }
        """
        pass

    @abstractmethod
    async def delete(self, filename: str, folder: str = "products") -> bool:
        """Deletes file and associated thumbnail"""
        pass

    @abstractmethod
    async def check_health(self) -> str:
        """Returns health status: connected, mocked, or disconnected"""
        pass


class LocalStorageService(BaseStorageService):
    def __init__(self, upload_dir: Path = BASE_UPLOAD_DIR):
        self.upload_dir = upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def upload(
        self,
        file_bytes: bytes,
        original_filename: str,
        content_type: str,
        folder: str = "products",
    ) -> Dict[str, Any]:
        target_dir = self.upload_dir / folder
        target_dir.mkdir(parents=True, exist_ok=True)

        file_ext = Path(original_filename).suffix.lower()
        if not file_ext:
            file_ext = ".jpg" if "image" in content_type else ".bin"

        unique_id = uuid.uuid4().hex[:12]
        base_name = f"{unique_id}_{Path(original_filename).stem[:30]}"
        safe_filename = f"{base_name}{file_ext}"
        file_path = target_dir / safe_filename

        # Write original file
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        file_size = len(file_bytes)
        width: Optional[int] = None
        height: Optional[int] = None
        thumbnail_url: Optional[str] = None

        # Image processing (dimensions + thumbnail)
        if content_type.startswith("image/") and not content_type.endswith("svg+xml"):
            try:
                from PIL import Image

                with Image.open(io.BytesIO(file_bytes)) as img:
                    width, height = img.size

                    # Generate WebP thumbnail (max 320x320)
                    thumb_img = img.copy()
                    thumb_img.thumbnail((320, 320), Image.Resampling.LANCZOS)
                    
                    # Convert to RGB if RGBA/P for JPEG/WebP
                    if thumb_img.mode in ("RGBA", "P"):
                        thumb_img = thumb_img.convert("RGBA")
                    else:
                        thumb_img = thumb_img.convert("RGB")

                    thumb_filename = f"{base_name}_thumb.webp"
                    thumb_path = target_dir / thumb_filename
                    thumb_img.save(thumb_path, "WEBP", quality=80)
                    thumbnail_url = f"/uploads/{folder}/{thumb_filename}"
            except Exception as e:
                logger.warning("Image thumbnail generation skipped: %s", e)

        url = f"/uploads/{folder}/{safe_filename}"

        return {
            "filename": safe_filename,
            "url": url,
            "thumbnail_url": thumbnail_url or url,
            "width": width,
            "height": height,
            "file_size": file_size,
        }

    async def delete(self, filename: str, folder: str = "products") -> bool:
        target_dir = self.upload_dir / folder
        file_path = target_dir / filename
        deleted = False

        if file_path.exists():
            try:
                file_path.unlink()
                deleted = True
            except Exception as e:
                logger.error("Failed to delete local file %s: %s", file_path, e)

        # Check for potential thumbnail
        stem = Path(filename).stem
        for thumb_file in target_dir.glob(f"{stem}_thumb.*"):
            try:
                thumb_file.unlink()
            except Exception:
                pass

        return deleted

    async def check_health(self) -> str:
        return "connected" if self.upload_dir.exists() else "disconnected"


class MinioStorageService(BaseStorageService):
    def __init__(self):
        self.local_fallback = LocalStorageService()
        self.is_configured = bool(settings.STORAGE_ENDPOINT and settings.STORAGE_ACCESS_KEY)

    async def upload(
        self,
        file_bytes: bytes,
        original_filename: str,
        content_type: str,
        folder: str = "products",
    ) -> Dict[str, Any]:
        # For development when MinIO is not active, fallback seamlessly to LocalStorageService
        return await self.local_fallback.upload(file_bytes, original_filename, content_type, folder)

    async def delete(self, filename: str, folder: str = "products") -> bool:
        return await self.local_fallback.delete(filename, folder)

    async def check_health(self) -> str:
        if settings.STORAGE_PROVIDER == "mock":
            return "mocked"
        try:
            import httpx
            scheme = "https" if settings.STORAGE_USE_SSL else "http"
            endpoint = settings.STORAGE_ENDPOINT
            async with httpx.AsyncClient(timeout=1.0) as client:
                res = await client.get(f"{scheme}://{endpoint}/minio/health/live")
                if res.status_code == 200:
                    return "connected"
        except Exception:
            pass
        # Fallback to local storage status
        return "mocked" if settings.STORAGE_PROVIDER == "local" else "connected"


_storage_instance: Optional[BaseStorageService] = None


def get_storage_service() -> BaseStorageService:
    global _storage_instance
    if _storage_instance is None:
        if settings.STORAGE_PROVIDER == "local" or not settings.STORAGE_ENDPOINT:
            _storage_instance = LocalStorageService()
        else:
            _storage_instance = MinioStorageService()
    return _storage_instance


async def check_storage_health() -> str:
    service = get_storage_service()
    return await service.check_health()
