from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.models.social import SocialConnection


@dataclass
class ConnectionValidationResult:
    is_valid: bool
    status: str  # CONNECTED, EXPIRED, ERROR
    error_message: Optional[str] = None
    account_info: Optional[Dict[str, Any]] = None


@dataclass
class PublishResult:
    success: bool
    external_post_id: Optional[str] = None
    external_post_url: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    can_retry: bool = True
    initial_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TokenRefreshResult:
    success: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None


class SocialProvider(ABC):
    """
    Abstract Social Provider Interface
    Defines the contract for multi-platform publishing adapters.
    """

    @property
    @abstractmethod
    def platform(self) -> str:
        """Name of the platform, e.g. FACEBOOK, INSTAGRAM, TIKTOK, ZALO_OA, WEBSITE_BLOG"""
        pass

    @abstractmethod
    async def validate_connection(self, connection: SocialConnection) -> ConnectionValidationResult:
        """Validates API token & permissions for the connected account."""
        pass

    @abstractmethod
    async def publish_text(
        self,
        content_payload: Dict[str, Any],
        connection: SocialConnection,
    ) -> PublishResult:
        """Publishes a pure text post / status update."""
        pass

    @abstractmethod
    async def publish_image(
        self,
        content_payload: Dict[str, Any],
        media_urls: List[str],
        connection: SocialConnection,
    ) -> PublishResult:
        """Publishes a post with single or carousel images."""
        pass

    @abstractmethod
    async def publish_video(
        self,
        content_payload: Dict[str, Any],
        video_url: str,
        connection: SocialConnection,
    ) -> PublishResult:
        """Publishes a video (Reels, TikTok video, Video post)."""
        pass

    @abstractmethod
    async def fetch_post_metrics(
        self,
        external_post_id: str,
        connection: SocialConnection,
    ) -> Dict[str, Any]:
        """Fetches post performance telemetry (impressions, reach, likes, comments, shares, clicks)."""
        pass

    @abstractmethod
    async def refresh_token(self, connection: SocialConnection) -> TokenRefreshResult:
        """Refreshes expired or expiring OAuth access token."""
        pass
