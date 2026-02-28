"""
Email notification metrics.

Tracks sent/failed email counts in Redis using daily rolling keys.

Usage:
    Read:  get_email_metrics()            ← called by the API endpoint
    Write: increment_email_sent()         ← call from SMTPEmailService.send_*
           increment_email_failed()       ← call from SMTPEmailService on exception

Key format:  email:sent:YYYY-MM-DD   →  int counter
             email:failed:YYYY-MM-DD →  int counter
TTL: 7 days (counters auto-expire)

Clean Architecture:
    Infrastructure layer — Redis counters only.
    No domain or application logic.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.infrastructure.cache.redis_client import get_redis

_SENT_PREFIX   = "email:sent"
_FAILED_PREFIX = "email:failed"
_TTL_SECONDS   = 86400 * 7  # 7 days


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


@dataclass(frozen=True)
class EmailMetrics:
    """Email service metrics for today."""
    service: str
    status: str
    sent_today: int
    failed_today: int
    note: str | None


async def get_email_metrics() -> EmailMetrics:
    """
    Read today's email sent/failed counters from Redis.

    Counters will read 0 until increment_email_sent() /
    increment_email_failed() are called from the email service.

    Returns:
        EmailMetrics with today's send statistics.
    """
    redis = await get_redis()

    sent_raw   = await redis.get(f"{_SENT_PREFIX}:{_today()}")
    failed_raw = await redis.get(f"{_FAILED_PREFIX}:{_today()}")

    return EmailMetrics(
        service="smtp",
        status="healthy",
        sent_today=int(sent_raw) if sent_raw else 0,
        failed_today=int(failed_raw) if failed_raw else 0,
        note=None,
    )


async def increment_email_sent() -> None:
    """Increment today's sent email counter. Call after successful send."""
    redis = await get_redis()
    key = f"{_SENT_PREFIX}:{_today()}"
    await redis.incr(key)
    await redis.expire(key, _TTL_SECONDS)


async def increment_email_failed() -> None:
    """Increment today's failed email counter. Call on send exception."""
    redis = await get_redis()
    key = f"{_FAILED_PREFIX}:{_today()}"
    await redis.incr(key)
    await redis.expire(key, _TTL_SECONDS)
