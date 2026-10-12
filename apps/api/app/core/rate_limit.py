import time
import logging
from collections import defaultdict
from fastapi import HTTPException, Request, status
from app.core.config import settings
from app.core.redis import redis_client

logger = logging.getLogger(__name__)

# Fallback in-memory rate limiting: ip -> list of timestamps
_in_memory_requests = defaultdict(list)


async def enforce_auth_rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:auth:{client_ip}"
    limit = settings.AUTH_RATE_LIMIT_PER_MINUTE
    window = 60  # seconds

    now = time.time()

    # Try Redis first
    if redis_client:
        try:
            current = await redis_client.incr(key)
            if current == 1:
                await redis_client.expire(key, window)
            if current > limit:
                logger.warning("Auth rate limit exceeded for IP: %s (count: %d)", client_ip, current)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Quá nhiều yêu cầu đăng nhập. Vui lòng thử lại sau 1 phút.",
                )
            return
        except HTTPException:
            raise
        except Exception as e:
            logger.debug("Redis rate limiter failed, falling back to memory: %s", e)

    # In-memory fallback
    timestamps = _in_memory_requests[client_ip]
    # Prune timestamps older than window
    cutoff = now - window
    _in_memory_requests[client_ip] = [t for t in timestamps if t > cutoff]

    if len(_in_memory_requests[client_ip]) >= limit:
        logger.warning("In-memory rate limit exceeded for IP: %s", client_ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Quá nhiều yêu cầu đăng nhập. Vui lòng thử lại sau 1 phút.",
        )

    _in_memory_requests[client_ip].append(now)
