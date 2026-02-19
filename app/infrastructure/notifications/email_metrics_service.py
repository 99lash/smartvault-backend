"""
Infrastructure implementation of EmailMetricsService.
Fetches email metrics from Redis (or other backend).
"""
from __future__ import annotations
from typing import Any
from app.application.ports.email_metrics_service import EmailMetrics, EmailMetricsService

import aioredis
import os

class RedisEmailMetrics:
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis = None

    async def _get_redis(self):
        if self._redis is None:
            self._redis = await aioredis.create_redis_pool(self.redis_url)
        return self._redis

    async def get_email_metrics(self) -> EmailMetrics:
        redis = await self._get_redis()
        sent = await redis.get("email:sent_today")
        failed = await redis.get("email:failed_today")
        return type("EmailMetricsObj", (), {
            "service": "email",
            "status": "ok",
            "sent_today": int(sent or 0),
            "failed_today": int(failed or 0),
            "note": None,
        })()
