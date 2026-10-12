from typing import Dict
from app.models.social import SocialPlatform
from app.services.social_providers.base import SocialProvider
from app.services.social_providers.mock_provider import MockSocialProvider
from app.services.social_providers.website_publisher import WebsitePublisher

_provider_cache: Dict[str, SocialProvider] = {}


def get_social_provider(platform_or_channel: str, is_mock: bool = True) -> SocialProvider:
    """
    Factory function returning the appropriate SocialProvider implementation.
    Supports platform-specific providers and internal website publisher.
    """
    normalized = platform_or_channel.upper()

    if normalized in ("WEBSITE_BLOG", "WEBSITE_BANNER", "WEBSITE"):
        key = "WEBSITE_BLOG"
        if key not in _provider_cache:
            _provider_cache[key] = WebsitePublisher()
        return _provider_cache[key]

    # Map aliases
    if normalized == "ZALO":
        normalized = SocialPlatform.ZALO_OA.value

    cache_key = f"{normalized}_{'mock' if is_mock else 'live'}"
    if cache_key not in _provider_cache:
        # Currently, all external social channels utilize the robust MockSocialProvider
        # until live production OAuth API credentials are provided by the client.
        _provider_cache[cache_key] = MockSocialProvider(platform_name=normalized)

    return _provider_cache[cache_key]
