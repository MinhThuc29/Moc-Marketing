import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func

from app.models.content import ContentItem, ContentStatus, ContentChannel
from app.models.social import (
    SocialConnection,
    PublishedPost,
    PostMetric,
    SocialPlatform,
    ConnectionStatus,
    PublishStatus,
)
from app.schemas.social import (
    SocialConnectionCreate,
    SocialConnectionUpdate,
)
from app.services.social_providers import get_social_provider

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SocialPublishingService:
    """
    Central Social Publishing & Multi-Platform Publishing Engine.
    Handles account connections, queue processing, background pickup,
    idempotent publishing, exponential backoff retries, and metrics sync.
    Operates asynchronously with AsyncSession.
    """

    # -------------------------------------------------------------
    # Social Connection Management
    # -------------------------------------------------------------

    @staticmethod
    async def list_connections(
        db: AsyncSession,
        platform: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[SocialConnection]:
        query = select(SocialConnection).order_by(desc(SocialConnection.created_at))
        if platform:
            query = query.where(SocialConnection.platform == platform.upper())
        if status:
            query = query.where(SocialConnection.status == status.upper())
        result = await db.scalars(query)
        return list(result.all())

    @staticmethod
    async def get_connection(db: AsyncSession, connection_id: str) -> Optional[SocialConnection]:
        return await db.scalar(select(SocialConnection).where(SocialConnection.id == connection_id))

    @staticmethod
    async def get_or_create_default_connection(db: AsyncSession, platform_or_channel: str) -> SocialConnection:
        """
        Retrieves active connection for the platform, or automatically creates
        a default Mock sandbox connection if none exists.
        """
        normalized = platform_or_channel.upper()
        if normalized == "ZALO":
            normalized = SocialPlatform.ZALO_OA.value
        elif normalized in ("WEBSITE_BANNER", "WEBSITE"):
            normalized = SocialPlatform.WEBSITE_BLOG.value

        conn = await db.scalar(
            select(SocialConnection).where(
                and_(
                    SocialConnection.platform == normalized,
                    SocialConnection.is_connected.is_(True),
                )
            ).order_by(desc(SocialConnection.created_at))
        )

        if conn:
            return conn

        # Create auto-provisioned mock connection
        name_map = {
            SocialPlatform.FACEBOOK.value: "Mộc Healthy Farm Fanpage",
            SocialPlatform.INSTAGRAM.value: "@moc.healthy.farm",
            SocialPlatform.TIKTOK.value: "@moc_healthy_food",
            SocialPlatform.ZALO_OA.value: "Mộc Healthy Official Account",
            SocialPlatform.WEBSITE_BLOG.value: "Mộc Healthy Storefront Blog",
        }
        account_name = name_map.get(normalized, f"Mộc Healthy {normalized}")
        account_id = f"acc_{normalized.lower()}_demo"

        new_conn = SocialConnection(
            platform=normalized,
            account_name=account_name,
            account_id=account_id,
            is_connected=True,
            status=ConnectionStatus.CONNECTED.value,
            is_mock=True,
            token_expires_at=utc_now() + timedelta(days=90),
            metadata_json={"auto_provisioned": True, "followers": 12500},
        )
        db.add(new_conn)
        await db.commit()
        await db.refresh(new_conn)
        return new_conn

    @staticmethod
    async def create_connection(db: AsyncSession, data: SocialConnectionCreate) -> SocialConnection:
        conn = SocialConnection(
            platform=data.platform.upper(),
            account_name=data.account_name,
            account_id=data.account_id,
            app_id=data.app_id,
            access_token=data.access_token,
            refresh_token=data.refresh_token,
            token_expires_at=data.token_expires_at or (utc_now() + timedelta(days=60)),
            is_connected=True,
            status=ConnectionStatus.CONNECTED.value,
            is_mock=data.is_mock,
            metadata_json=data.metadata_json or {},
        )
        db.add(conn)
        await db.commit()
        await db.refresh(conn)
        return conn

    @staticmethod
    async def update_connection(
        db: AsyncSession,
        connection_id: str,
        data: SocialConnectionUpdate,
    ) -> Optional[SocialConnection]:
        conn = await SocialPublishingService.get_connection(db, connection_id)
        if not conn:
            return None

        if data.account_name is not None:
            conn.account_name = data.account_name
        if data.access_token is not None:
            conn.access_token = data.access_token
        if data.refresh_token is not None:
            conn.refresh_token = data.refresh_token
        if data.token_expires_at is not None:
            conn.token_expires_at = data.token_expires_at
        if data.is_connected is not None:
            conn.is_connected = data.is_connected
        if data.status is not None:
            conn.status = data.status
        if data.metadata_json is not None:
            conn.metadata_json = data.metadata_json

        conn.updated_at = utc_now()
        await db.commit()
        await db.refresh(conn)
        return conn

    @staticmethod
    async def test_connection(db: AsyncSession, connection_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        conn = await SocialPublishingService.get_connection(db, connection_id)
        if not conn:
            return False, "Không tìm thấy kết nối tài khoản mạng xã hội.", None

        provider = get_social_provider(conn.platform, is_mock=conn.is_mock)
        res = await provider.validate_connection(conn)

        conn.status = res.status
        conn.is_connected = res.is_valid
        conn.updated_at = utc_now()
        await db.commit()

        msg = "Kết nối hợp lệ và sẵn sàng xuất bản." if res.is_valid else (res.error_message or "Kết nối không hợp lệ.")
        return res.is_valid, msg, res.account_info

    @staticmethod
    async def refresh_connection_token(db: AsyncSession, connection_id: str) -> Tuple[bool, str, Optional[datetime]]:
        conn = await SocialPublishingService.get_connection(db, connection_id)
        if not conn:
            return False, "Không tìm thấy kết nối.", None

        provider = get_social_provider(conn.platform, is_mock=conn.is_mock)
        res = await provider.refresh_token(conn)

        if res.success:
            conn.access_token = res.access_token or conn.access_token
            if res.expires_at:
                conn.token_expires_at = res.expires_at
            conn.status = ConnectionStatus.CONNECTED.value
            conn.is_connected = True
            conn.updated_at = utc_now()
            await db.commit()
            return True, "Làm mới Token thành công.", conn.token_expires_at
        else:
            return False, res.error_message or "Làm mới Token thất bại.", None

    @staticmethod
    async def disconnect(db: AsyncSession, connection_id: str) -> bool:
        conn = await SocialPublishingService.get_connection(db, connection_id)
        if not conn:
            return False
        conn.is_connected = False
        conn.status = ConnectionStatus.DISCONNECTED.value
        conn.updated_at = utc_now()
        await db.commit()
        return True

    # -------------------------------------------------------------
    # Publishing Engine & Queue Flow
    # -------------------------------------------------------------

    @staticmethod
    async def publish_content_now(
        db: AsyncSession,
        content_id: str,
        connection_id: Optional[str] = None,
        simulate_failure: bool = False,
        failure_reason: Optional[str] = None,
    ) -> PublishedPost:
        """
        Executes end-to-end publishing of a content item:
        1. Validates content approval status.
        2. Enforces Idempotency (does not double publish already published items).
        3. Retrieves or defaults social connection.
        4. Transitions state to PUBLISHING.
        5. Calls platform provider adapter.
        6. On success: marks PUBLISHED, saves external post IDs, records initial metric snapshot.
        7. On error: marks FAILED, increments retry count, schedules next exponential backoff retry.
        """
        content = await db.scalar(select(ContentItem).where(ContentItem.id == content_id))
        if not content:
            raise ValueError(f"Không tìm thấy bài viết ID {content_id}")

        # Idempotency check: if already published, return existing PublishedPost
        existing_post = await db.scalar(
            select(PublishedPost).where(
                and_(
                    PublishedPost.content_id == content_id,
                    PublishedPost.publish_status == PublishStatus.PUBLISHED.value,
                )
            ).order_by(desc(PublishedPost.published_at))
        )
        if existing_post:
            logger.info("Idempotent check hit: Content %s is already published as %s", content_id, existing_post.id)
            return existing_post

        # Verify allowed status
        allowed_statuses = (
            ContentStatus.APPROVED.value,
            ContentStatus.SCHEDULED.value,
            ContentStatus.FAILED.value,
            ContentStatus.PUBLISHING.value,
        )
        if content.status not in allowed_statuses:
            raise ValueError(
                f"Bài viết đang ở trạng thái '{content.status}'. Phải ở trạng thái APPROVED hoặc SCHEDULED mới có thể xuất bản."
            )

        # Retrieve connection
        conn = None
        if connection_id:
            conn = await SocialPublishingService.get_connection(db, connection_id)
        if not conn:
            conn = await SocialPublishingService.get_or_create_default_connection(db, content.channel)

        # Get or create PublishedPost entry
        published_post = await db.scalar(
            select(PublishedPost).where(
                and_(
                    PublishedPost.content_id == content_id,
                    PublishedPost.publish_status.in_([
                        PublishStatus.PENDING.value,
                        PublishStatus.QUEUED.value,
                        PublishStatus.PUBLISHING.value,
                        PublishStatus.FAILED.value,
                    ]),
                )
            ).order_by(desc(PublishedPost.created_at))
        )

        if not published_post:
            published_post = PublishedPost(
                content_id=content.id,
                connection_id=conn.id,
                channel=content.channel,
                publish_status=PublishStatus.PUBLISHING.value,
                scheduled_at=content.scheduled_at,
                payload_snapshot={
                    "title": content.title,
                    "hook": content.hook,
                    "body": content.body,
                    "cta": content.cta,
                    "hashtags": content.hashtags,
                    "media_asset_ids": content.media_asset_ids,
                },
            )
            db.add(published_post)
        else:
            published_post.connection_id = conn.id
            published_post.publish_status = PublishStatus.PUBLISHING.value

        # Update Content Item status
        content.status = ContentStatus.PUBLISHING.value
        await db.commit()
        await db.refresh(published_post)

        # Prepare payload
        payload = {
            "title": content.title,
            "hook": content.hook,
            "body": content.body,
            "cta": content.cta,
            "hashtags": content.hashtags,
        }
        if simulate_failure:
            payload["__simulate_failure__"] = True
            payload["__failure_reason__"] = failure_reason or "Simulated social provider error"

        provider = get_social_provider(content.channel, is_mock=conn.is_mock)

        # Dispatch based on media attachments
        media_list = content.media_asset_ids or []
        try:
            if content.content_type in ("TIKTOK_SCRIPT", "REEL_SCRIPT") and media_list:
                result = await provider.publish_video(payload, media_list[0], conn)
            elif media_list:
                result = await provider.publish_image(payload, media_list, conn)
            else:
                result = await provider.publish_text(payload, conn)
        except Exception as exc:
            logger.exception("Provider publish exception for content %s: %s", content_id, exc)
            result = None
            error_msg = str(exc)

        now = utc_now()
        if result and result.success:
            # Publish Success
            published_post.publish_status = PublishStatus.PUBLISHED.value
            published_post.external_post_id = result.external_post_id
            published_post.external_post_url = result.external_post_url
            published_post.published_at = now
            published_post.error_message = None
            published_post.error_code = None
            published_post.next_retry_at = None

            content.status = ContentStatus.PUBLISHED.value
            content.published_at = now
            content.external_post_id = result.external_post_id
            content.external_post_url = result.external_post_url
            content.error_message = None
            content.metrics = result.initial_metrics or {}

            # Create initial metric record
            metric_data = result.initial_metrics or {}
            metric = PostMetric(
                published_post_id=published_post.id,
                recorded_at=now,
                impressions=metric_data.get("impressions", metric_data.get("views", 0)),
                reach=metric_data.get("reach", metric_data.get("delivered", 0)),
                likes=metric_data.get("likes", 0),
                comments=metric_data.get("comments", 0),
                shares=metric_data.get("shares", 0),
                clicks=metric_data.get("clicks", metric_data.get("cta_clicks", 0)),
                conversions=metric_data.get("conversions", 0),
                raw_data_json=metric_data,
            )
            db.add(metric)

        else:
            # Publish Failed
            err_text = result.error_message if result else error_msg
            published_post.publish_status = PublishStatus.FAILED.value
            published_post.error_message = err_text
            published_post.error_code = result.error_code if result else "UNKNOWN_ERROR"
            published_post.retry_count += 1

            # Exponential backoff: 2^retry minutes (e.g. 2m, 4m, 8m...)
            delay_minutes = 2 ** min(published_post.retry_count, 5)
            published_post.next_retry_at = now + timedelta(minutes=delay_minutes)

            content.status = ContentStatus.FAILED.value
            content.error_message = err_text
            content.retry_count = published_post.retry_count

        published_post.updated_at = now
        content.updated_at = now
        await db.commit()
        await db.refresh(published_post)
        return published_post

    @staticmethod
    async def pickup_and_publish_due_batch(
        db: AsyncSession,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Background Worker batch execution:
        1. Finds scheduled content due for publishing (scheduled_at <= now()).
        2. Finds failed posts eligible for retry (retry_count < max_retries and next_retry_at <= now()).
        3. Publishes due posts and compiles telemetry.
        """
        now = utc_now()
        processed = 0
        published = 0
        retried = 0
        failed = 0
        details = []

        # 1. Pickup due scheduled content
        due_contents_res = await db.scalars(
            select(ContentItem).where(
                and_(
                    ContentItem.status == ContentStatus.SCHEDULED.value,
                    ContentItem.scheduled_at.is_not(None),
                    ContentItem.scheduled_at <= now,
                )
            ).order_by(ContentItem.scheduled_at).limit(limit)
        )
        due_contents = list(due_contents_res.all())

        for content in due_contents:
            try:
                res_post = await SocialPublishingService.publish_content_now(db, content.id)
                processed += 1
                if res_post.publish_status == PublishStatus.PUBLISHED.value:
                    published += 1
                    status_str = "SUCCESS"
                else:
                    failed += 1
                    status_str = "FAILED"
                details.append({
                    "content_id": content.id,
                    "title": content.title,
                    "channel": content.channel,
                    "type": "SCHEDULED_PICKUP",
                    "status": status_str,
                    "post_id": res_post.external_post_id,
                })
            except Exception as e:
                logger.error("Error processing scheduled content %s: %s", content.id, e)
                failed += 1
                details.append({
                    "content_id": content.id,
                    "title": content.title,
                    "status": "ERROR",
                    "error": str(e),
                })

        # 2. Pickup eligible failed posts for retry
        remaining_slots = limit - processed
        if remaining_slots > 0:
            retry_posts_res = await db.scalars(
                select(PublishedPost).where(
                    and_(
                        PublishedPost.publish_status == PublishStatus.FAILED.value,
                        PublishedPost.retry_count < PublishedPost.max_retries,
                        PublishedPost.next_retry_at.is_not(None),
                        PublishedPost.next_retry_at <= now,
                    )
                ).order_by(PublishedPost.next_retry_at).limit(remaining_slots)
            )
            retry_posts = list(retry_posts_res.all())

            for post in retry_posts:
                try:
                    res_post = await SocialPublishingService.publish_content_now(
                        db,
                        post.content_id,
                        connection_id=post.connection_id,
                    )
                    processed += 1
                    retried += 1
                    if res_post.publish_status == PublishStatus.PUBLISHED.value:
                        published += 1
                        status_str = "SUCCESS"
                    else:
                        failed += 1
                        status_str = "FAILED"
                    details.append({
                        "content_id": post.content_id,
                        "published_post_id": post.id,
                        "type": "RETRY_PICKUP",
                        "status": status_str,
                        "retry_count": res_post.retry_count,
                    })
                except Exception as e:
                    logger.error("Error retrying post %s: %s", post.id, e)
                    failed += 1
                    details.append({
                        "published_post_id": post.id,
                        "status": "ERROR",
                        "error": str(e),
                    })

        return {
            "processed": processed,
            "published": published,
            "retried": retried,
            "failed": failed,
            "details": details,
        }

    @staticmethod
    async def retry_failed_post(db: AsyncSession, published_post_id: str) -> PublishedPost:
        """Manual trigger to retry a failed publication immediately."""
        post = await db.scalar(select(PublishedPost).where(PublishedPost.id == published_post_id))
        if not post:
            raise ValueError(f"Không tìm thấy bản ghi xuất bản ID {published_post_id}")
        return await SocialPublishingService.publish_content_now(
            db,
            content_id=post.content_id,
            connection_id=post.connection_id,
        )

    @staticmethod
    async def sync_post_metrics(db: AsyncSession, published_post_id: str) -> PostMetric:
        """Syncs the latest performance metrics from provider API and stores new timeseries entry."""
        post = await db.scalar(select(PublishedPost).where(PublishedPost.id == published_post_id))
        if not post:
            raise ValueError(f"Không tìm thấy bản ghi xuất bản ID {published_post_id}")
        if not post.external_post_id:
            raise ValueError("Bản ghi chưa có external_post_id, không thể đồng bộ chỉ số.")

        conn = post.connection
        if not conn:
            conn = await SocialPublishingService.get_or_create_default_connection(db, post.channel)

        provider = get_social_provider(post.channel, is_mock=conn.is_mock)
        fresh_metrics = await provider.fetch_post_metrics(post.external_post_id, conn)

        now = utc_now()
        new_metric = PostMetric(
            published_post_id=post.id,
            recorded_at=now,
            impressions=fresh_metrics.get("impressions", fresh_metrics.get("views", 0)),
            reach=fresh_metrics.get("reach", fresh_metrics.get("reads", fresh_metrics.get("delivered", 0))),
            likes=fresh_metrics.get("likes", 0),
            comments=fresh_metrics.get("comments", 0),
            shares=fresh_metrics.get("shares", 0),
            clicks=fresh_metrics.get("clicks", fresh_metrics.get("cta_clicks", 0)),
            conversions=fresh_metrics.get("conversions", 0),
            raw_data_json=fresh_metrics,
        )
        db.add(new_metric)

        # Update content snapshot
        if post.content:
            post.content.metrics = fresh_metrics
            post.content.updated_at = now

        await db.commit()
        await db.refresh(new_metric)
        return new_metric

    @staticmethod
    async def list_published_posts(
        db: AsyncSession,
        channel: Optional[str] = None,
        status: Optional[str] = None,
        content_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[PublishedPost], int]:
        query = select(PublishedPost).order_by(desc(PublishedPost.created_at))
        count_query = select(func.count()).select_from(PublishedPost)

        if channel:
            query = query.where(PublishedPost.channel == channel.upper())
            count_query = count_query.where(PublishedPost.channel == channel.upper())
        if status:
            query = query.where(PublishedPost.publish_status == status.upper())
            count_query = count_query.where(PublishedPost.publish_status == status.upper())
        if content_id:
            query = query.where(PublishedPost.content_id == content_id)
            count_query = count_query.where(PublishedPost.content_id == content_id)

        total = (await db.scalar(count_query)) or 0
        items_res = await db.scalars(query.offset((page - 1) * limit).limit(limit))
        return list(items_res.all()), total

    @staticmethod
    async def get_published_post(db: AsyncSession, published_post_id: str) -> Optional[PublishedPost]:
        return await db.scalar(select(PublishedPost).where(PublishedPost.id == published_post_id))
