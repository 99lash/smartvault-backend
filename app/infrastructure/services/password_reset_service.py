from __future__ import annotations

import secrets
from redis.exceptions import ResponseError

from app.core.settings import settings
from app.infrastructure.cache.redis_client import (
    get_redis,
    redis_setex,
)

class PasswordResetService:
    _CONSUME_LUA = """
local current = redis.call('GET', KEYS[1])
if not current then return nil end
-- prefer GETDEL when available (Redis >= 6.2)
local ok, val = pcall(redis.call, 'GETDEL', KEYS[1])
if ok then
  return val
end
redis.call('DEL', KEYS[1])
return current
"""

    def _token_key(self, token: str) -> str:
        return f"pwd_reset:{token}"

    async def issue_token(self, email: str) -> str:
        token = secrets.token_urlsafe(32)
        await redis_setex(
            self._token_key(token),
            settings.PASSWORD_RESET_TTL_SECONDS,
            email.lower().encode("utf-8"),
        )
        return token

    async def consume_token(self, token: str) -> str | None:
        """Atomically read-and-delete the reset token.

        Returns:
            str: the email associated with the token if matched and deleted
            None: when token is missing/expired
        """
        key = self._token_key(token)
        redis = await get_redis()
        try:
            result = await redis.eval(self._CONSUME_LUA, 1, key)
            if isinstance(result, bytes):
                return result.decode("utf-8")
            return result
        except ResponseError:
            # Fallback if EVAL is disabled: best-effort match then delete
            value = await redis.get(key)
            if value is None:
                return None
            await redis.delete(key)
            return value.decode("utf-8")
