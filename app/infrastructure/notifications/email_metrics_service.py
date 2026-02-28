"""
Infrastructure implementation of EmailMetricsService.
Fetches email metrics from Redis (or other backend).
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from app.infrastructure.notifications.email_metrics import get_email_metrics as fetch_redis_metrics

if TYPE_CHECKING:
    from app.application.ports.email_metrics_service import EmailMetrics

class RedisEmailMetrics:
    """
    Implementation of EmailMetricsService using Redis.
    Delegates to the low-level Redis metrics functions.
    """
    async def get_email_metrics(self) -> EmailMetrics:
        # Delegate to the function in email_metrics.py which handles keys and Redis connection correctly
        return await fetch_redis_metrics()
