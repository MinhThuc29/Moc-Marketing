import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from app.models.social import SocialConnection, SocialPlatform
from app.services.social_providers.base import (
    SocialProvider,
    ConnectionValidationResult,
    PublishResult,
    TokenRefreshResult,
)


class MockSocialProvider(SocialProvider):
    """
    Robust Mock / Sandbox Social Media Provider.
    Implements full platform simulation without needing external API credentials.
    Supports Facebook, Instagram, TikTok, Zalo OA with deterministic mock behaviors.
    """

    def __init__(self, platform_name: str = SocialPlatform.FACEBOOK.value):
        self._platform = platform_name.upper()

    @property
    def platform(self) -> str:
        return self._platform

    async def validate_connection(self, connection: SocialConnection) -> ConnectionValidationResult:
        await asyncio.sleep(0.01)  # Simulate network latency

        if not connection.is_connected or connection.status == "DISCONNECTED":
            return ConnectionValidationResult(
                is_valid=False,
                status="DISCONNECTED",
                error_message="Tài khoản chưa được kết nối hoặc đã bị ngắt kết nối.",
            )

        if connection.token_expires_at:
            exp_dt = (
                connection.token_expires_at.replace(tzinfo=timezone.utc)
                if connection.token_expires_at.tzinfo is None
                else connection.token_expires_at
            )
            if exp_dt < datetime.now(timezone.utc):
                return ConnectionValidationResult(
                    is_valid=False,
                    status="EXPIRED",
                    error_message="OAuth Access Token đã hết hạn. Vui lòng làm mới token.",
                )

        # Mock healthy account details
        account_info = {
            "account_id": connection.account_id,
            "account_name": connection.account_name,
            "platform": self._platform,
            "followers_count": 18450,
            "verified": True,
            "permissions": ["pages_manage_posts", "pages_read_engagement", "publish_video"],
            "mock_mode": True,
        }

        return ConnectionValidationResult(
            is_valid=True,
            status="CONNECTED",
            account_info=account_info,
        )

    async def publish_text(
        self,
        content_payload: Dict[str, Any],
        connection: SocialConnection,
    ) -> PublishResult:
        return await self._execute_mock_publish(content_payload, connection, post_type="TEXT")

    async def publish_image(
        self,
        content_payload: Dict[str, Any],
        media_urls: List[str],
        connection: SocialConnection,
    ) -> PublishResult:
        payload_with_media = {**content_payload, "media_urls": media_urls}
        return await self._execute_mock_publish(payload_with_media, connection, post_type="IMAGE")

    async def publish_video(
        self,
        content_payload: Dict[str, Any],
        video_url: str,
        connection: SocialConnection,
    ) -> PublishResult:
        payload_with_video = {**content_payload, "video_url": video_url}
        return await self._execute_mock_publish(payload_with_video, connection, post_type="VIDEO")

    async def _execute_mock_publish(
        self,
        content_payload: Dict[str, Any],
        connection: SocialConnection,
        post_type: str,
    ) -> PublishResult:
        await asyncio.sleep(0.02)  # Simulate API network roundtrip

        # Configurable failure simulation for testing retries
        if content_payload.get("__simulate_failure__") is True:
            return PublishResult(
                success=False,
                error_message=content_payload.get("__failure_reason__", "Simulated platform rate limit or network timeout"),
                error_code="RATE_LIMIT_EXCEEDED",
                can_retry=True,
            )

        short_id = uuid.uuid4().hex[:10]
        platform_lower = self._platform.lower()

        if "FACEBOOK" in self._platform:
            post_id = f"fb_{short_id}"
            url = f"https://facebook.com/mochealthy/posts/{post_id}"
            metrics = {"reach": 240, "impressions": 450, "likes": 32, "comments": 8, "shares": 5, "clicks": 38, "conversions": 3}
        elif "INSTAGRAM" in self._platform:
            post_id = f"ig_{short_id}"
            url = f"https://instagram.com/p/{post_id}"
            metrics = {"reach": 380, "impressions": 520, "likes": 64, "comments": 14, "shares": 11, "clicks": 42, "conversions": 4}
        elif "TIKTOK" in self._platform:
            post_id = f"tt_{short_id}"
            url = f"https://tiktok.com/@moc_healthy/video/{post_id}"
            metrics = {"reach": 1200, "impressions": 2800, "likes": 210, "comments": 35, "shares": 58, "clicks": 110, "conversions": 12}
        elif "ZALO" in self._platform:
            post_id = f"zalo_oa_{short_id}"
            url = f"https://oa.zalo.me/post/{post_id}"
            metrics = {"reach": 500, "impressions": 620, "likes": 40, "comments": 12, "shares": 9, "clicks": 85, "conversions": 8}
        else:
            post_id = f"mock_{platform_lower}_{short_id}"
            url = f"https://mochealthy.vn/social/{platform_lower}/{post_id}"
            metrics = {"reach": 100, "impressions": 150, "likes": 10, "comments": 2, "shares": 1, "clicks": 15, "conversions": 1}

        return PublishResult(
            success=True,
            external_post_id=post_id,
            external_post_url=url,
            initial_metrics=metrics,
        )

    async def fetch_post_metrics(
        self,
        external_post_id: str,
        connection: SocialConnection,
    ) -> Dict[str, Any]:
        await asyncio.sleep(0.01)
        # Deterministic engagement growth based on ID hash
        hash_seed = abs(hash(external_post_id)) % 50
        return {
            "impressions": 500 + hash_seed * 20,
            "reach": 350 + hash_seed * 15,
            "likes": 45 + hash_seed * 2,
            "comments": 12 + (hash_seed % 10),
            "shares": 8 + (hash_seed % 8),
            "clicks": 60 + hash_seed * 3,
            "conversions": 5 + (hash_seed % 5),
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }

    async def refresh_token(self, connection: SocialConnection) -> TokenRefreshResult:
        await asyncio.sleep(0.01)
        new_token = f"mock_token_{uuid.uuid4().hex[:16]}"
        new_expires_at = datetime.now(timezone.utc) + timedelta(days=60)

        return TokenRefreshResult(
            success=True,
            access_token=new_token,
            expires_at=new_expires_at,
        )
