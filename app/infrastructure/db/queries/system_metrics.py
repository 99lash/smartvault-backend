"""
System and infrastructure metrics queries.

Clean Architecture:
    Infrastructure layer only. Called by API layer for read-only ops.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session
from redis.asyncio import Redis

from app.infrastructure.cache.redis_client import get_redis

# =============================================================================
# REDIS HEALTH METRICS
# =============================================================================


@dataclass(frozen=True)
class RedisHealthMetrics:
    """Redis health and statistics."""
    status: str  # "healthy" | "unhealthy"
    connected: bool
    memory_used_mb: float
    total_keys: int
    uptime_seconds: int


async def get_redis_health() -> RedisHealthMetrics:
    """Query Redis for health metrics."""
    try:
        redis: Redis = await get_redis()
        await redis.ping()
        info = await redis.info()
        memory_info = await redis.info("memory")
        total_keys = await redis.dbsize()

        return RedisHealthMetrics(
            status="healthy",
            connected=True,
            memory_used_mb=memory_info.get("used_memory", 0) / (1024 * 1024),
            total_keys=total_keys,
            uptime_seconds=info.get("uptime_in_seconds", 0),
        )
    except Exception:
        return RedisHealthMetrics(
            status="unhealthy",
            connected=False,
            memory_used_mb=0.0,
            total_keys=0,
            uptime_seconds=0,
        )


# =============================================================================
# DATABASE POOL METRICS
# =============================================================================


@dataclass(frozen=True)
class DatabasePoolMetrics:
    """Database connection pool statistics."""
    status: str
    pool_size: int
    checked_out: int
    overflow: int


def get_database_pool_metrics(db: Session) -> DatabasePoolMetrics:
    """Get SQLAlchemy connection pool statistics (sync)."""
    try:
        engine = db.get_bind()
        pool = engine.pool
        return DatabasePoolMetrics(
            status="healthy",
            pool_size=pool.size(),
            checked_out=pool.checkedout(),
            overflow=pool.overflow(),
        )
    except Exception:
        return DatabasePoolMetrics(
            status="unknown",
            pool_size=0,
            checked_out=0,
            overflow=0,
        )
