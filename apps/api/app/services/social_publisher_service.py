import uuid
from typing import Dict, Any, Tuple
from app.models.content import ContentItem, ContentChannel


class SocialPublisherService:
    """
    Multi-channel Social Media Publisher Service
    Dispatches content to provider adapters (Facebook, Zalo, TikTok, Instagram, Web Banner).
    In development/testing mode, uses robust Mock Social Adapters compliant with PLAN.md Section 17.
    """

    @staticmethod
    def publish(item: ContentItem) -> Tuple[bool, str, str, Dict[str, Any]]:
        """
        Publishes a ContentItem to its configured channel.
        Returns: (success: bool, external_post_id: str, external_post_url: str, initial_metrics: dict)
        """
        short_id = uuid.uuid4().hex[:10]
        channel = item.channel.upper()

        if channel == ContentChannel.FACEBOOK.value:
            post_id = f"fb_{short_id}"
            url = f"https://facebook.com/mochealthy/posts/{post_id}"
            metrics = {"reach": 150, "impressions": 280, "likes": 18, "shares": 3, "clicks": 24}
            return True, post_id, url, metrics

        elif channel == ContentChannel.ZALO.value:
            post_id = f"zalo_oa_{short_id}"
            url = f"https://oa.zalo.me/post/{post_id}"
            metrics = {"delivered": 200, "opened": 110, "cta_clicks": 35}
            return True, post_id, url, metrics

        elif channel == ContentChannel.TIKTOK.value:
            post_id = f"tt_video_{short_id}"
            url = f"https://tiktok.com/@mochealthy/video/{post_id}"
            metrics = {"views": 1250, "likes": 88, "shares": 14, "profile_visits": 42}
            return True, post_id, url, metrics

        elif channel == ContentChannel.INSTAGRAM.value:
            post_id = f"ig_{short_id}"
            url = f"https://instagram.com/p/{post_id}"
            metrics = {"reach": 310, "likes": 45, "saves": 12, "comments": 6}
            return True, post_id, url, metrics

        elif channel == ContentChannel.WEBSITE_BANNER.value:
            post_id = f"web_banner_{short_id}"
            url = f"https://mochanh.vn/?banner={post_id}"
            metrics = {"impressions": 850, "banner_clicks": 95}
            return True, post_id, url, metrics

        else:
            # Fallback for generic / SMS / EMAIL
            post_id = f"ext_{channel.lower()}_{short_id}"
            url = f"https://mochanh.vn/promotions/{post_id}"
            metrics = {"sent": 50, "delivered": 48}
            return True, post_id, url, metrics
