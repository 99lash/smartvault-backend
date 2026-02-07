from __future__ import annotations

from app.application.ports.pin_attempt_tracker import PINAttemptTracker
from app.domain.value_objects.pin_attempt_result import PINAttemptResult
from app.infrastructure.cache.redis_client import get_redis


class RedisPINAttemptTracker(PINAttemptTracker):
    """Redis-backed tracker for PIN entry attempts and lockout enforcement."""

    def __init__(self, max_attempts: int = 5, lockout_seconds: int = 300) -> None:
        self._max_attempts = max_attempts
        self._lockout_seconds = lockout_seconds

    def _key(self, vault_id: str) -> str:
        return f"pin_attempts:{vault_id}"

    async def register_failure(self, vault_id: str) -> tuple[PINAttemptResult, int | None]:
        redis = await get_redis()
        key = self._key(vault_id)

        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, self._lockout_seconds)
        else:
            ttl = await redis.ttl(key)
            if ttl == -1:
                await redis.expire(key, self._lockout_seconds)

        if count >= self._max_attempts:
            # Ensure lockout window is applied
            await redis.expire(key, self._lockout_seconds)
            return PINAttemptResult.LOCKED_OUT, 0

        attempts_remaining = self._max_attempts - count
        return PINAttemptResult.INVALID, attempts_remaining

    async def register_success(self, vault_id: str) -> None:
        redis = await get_redis()
        await redis.delete(self._key(vault_id))

    async def is_locked_out(self, vault_id: str) -> bool:
        redis = await get_redis()
        value = await redis.get(self._key(vault_id))
        if value is None:
            return False
        try:
            count = int(value)
        except (TypeError, ValueError):
            return False
        return count >= self._max_attempts
