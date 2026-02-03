from __future__ import annotations

from typing import Optional
from redis.asyncio import Redis
from app.core.settings import settings

_redis: Redis | None = None


def _redis_url() -> str:
    # Settings field should be REDIS_URL
    return str(settings.REDIS_URL)


async def get_redis() -> Redis:
    """
    Dependency provider for FastAPI.
    Uses a singleton client per process.
    """
    global _redis
    if _redis is None:
        _redis = Redis.from_url(_redis_url(), decode_responses=False)
    return _redis


async def redis_startup() -> None:
    """
    Connect/ping early so the app fails fast if Redis is unavailable.
    """
    r = await get_redis()
    await r.ping()


async def redis_shutdown() -> None:
    """
    Close client connections cleanly on shutdown.
    """
    global _redis
    if _redis is not None:
        await _redis.close()
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