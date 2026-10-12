import logging
from redis import asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)

redis_client = None

try:
    redis_client = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
except Exception as e:
    logger.warning("Failed to initialize Redis client: %s", e)


async def check_redis_health() -> str:
    if not redis_client:
        return "disconnected"
    try:
        ping = await redis_client.ping()
        return "connected" if ping else "disconnected"
    except Exception as e:
        logger.debug("Redis ping failed: %s", e)
        return "disconnected"
