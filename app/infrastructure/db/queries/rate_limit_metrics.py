"""
Rate limit metrics queries.

Scans Redis for active rate_limit:* keys set by RateLimiter and
aggregates violator counts and category breakdowns.

Clean Architecture:
    Infrastructure layer — reads from Redis (async) directly.
    Matches the async pattern used by RateLimiter in rate_limiter.py.
    No domain or application logic.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.infrastructure.cache.redis_client import get_redis


@dataclass(frozen=True)
class RateLimitViolator:
    """A single active rate-limited key."""
    key: str
    current_count: int
    ttl_seconds: int


@dataclass(frozen=True)
class RateLimitMetrics:
    """Aggregated rate limit statistics."""
    total_active_keys: int
    top_violators: list[RateLimitViolator]
    by_category: dict[str, int]


async def get_rate_limit_metrics() -> RateLimitMetrics:
    """
    Scan Redis for rate_limit:* keys and aggregate statistics.

    Key format set by RateLimiter: rate_limit:<key>
    where <key> is typically <category>:<identifier>.

    Returns:
        RateLimitMetrics with top 10 violators sorted by count
        and a category breakdown.
    """
    redis = await get_redis()

    violators: list[RateLimitViolator] = []
    by_category: dict[str, int] = {}
    total_keys = 0

    cursor = 0
    while True:
        cursor, keys = await redis.scan(
            cursor=cursor, match=b"rate_limit:*", count=100
        )

        for raw_key in keys:
            key_str = (
                raw_key.decode("utf-8") if isinstance(raw_key, bytes) else raw_key
            )
            # Strip prefix: "rate_limit:pin:unlock:user-123" → "pin:unlock:user-123"
            stripped = key_str.removeprefix("rate_limit:")

            # Category = first segment after prefix
            category = stripped.split(":")[0] if stripped else "unknown"
            by_category[category] = by_category.get(category, 0) + 1

            raw_count = await redis.get(raw_key)
            ttl = await redis.ttl(raw_key)

            if raw_count and ttl > 0:
                violators.append(
                    RateLimitViolator(
                        key=stripped,
                        current_count=int(raw_count),
                        ttl_seconds=int(ttl),
                    )
                )
            total_keys += 1

        if cursor == 0:
            break

    violators.sort(key=lambda v: v.current_count, reverse=True)

    return RateLimitMetrics(
        total_active_keys=total_keys,
        top_violators=violators[:10],
        by_category=by_category,
    )
