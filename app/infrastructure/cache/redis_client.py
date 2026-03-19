from __future__ import annotations

import asyncio
from typing import Optional
from urllib.parse import urlparse

from redis.asyncio import Redis

from app.core.logging import get_logger
from app.core.settings import settings

logger = get_logger(__name__)

_redis: Redis | None = None


def _redis_url() -> str:
    # Settings field should be REDIS_URL
    return str(settings.REDIS_URL)


def _redacted_redis_url() -> str:
    try:
        parsed = urlparse(_redis_url())
        scheme = parsed.scheme or "redis"
        host = parsed.hostname or ""
        port = parsed.port
        if port:
            return f"{scheme}://{host}:{port}"
        return f"{scheme}://{host}"
    except Exception:
        return "redis://[redacted]"


async def get_redis() -> Redis:
    """
    Dependency provider for FastAPI.
    Uses a singleton client per process.
    """
    global _redis
    if _redis is None:
        _redis = Redis.from_url(
            _redis_url(),
            decode_responses=False,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )
    return _redis


async def redis_startup() -> None:
    """
    Connect/ping early so the app fails fast if Redis is unavailable.
    """
    logger.info("redis_startup_begin", url=_redacted_redis_url())
    r = await get_redis()
    try:
        await asyncio.wait_for(r.ping(), timeout=5.0)
        logger.info("redis_ping_success")
    except asyncio.TimeoutError:
        logger.error("redis_ping_timeout", url=_redacted_redis_url())
        raise
    except Exception as exc:
        logger.error(
            "redis_ping_failed",
            url=_redacted_redis_url(),
            error=str(exc),
            error_type=type(exc).__name__,
        )
        raise


async def redis_shutdown() -> None:
    """
    Close client connections cleanly on shutdown.
    """
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None

# --- helpers ---

async def redis_setex(key: str, ttl_seconds: int, value: bytes) -> None:
    r = await get_redis()
    await r.setex(key, ttl_seconds, value)

async def redis_get(key: str) -> Optional[bytes]:
    r = await get_redis()
    v = await r.get(key)
    return v  # bytes | None

async def redis_del(key: str) -> int:
    r = await get_redis()
    return int(await r.delete(key))
