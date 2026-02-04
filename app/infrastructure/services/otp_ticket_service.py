from __future__ import annotations

import secrets
from dataclasses import dataclass

from redis.exceptions import ResponseError

from app.core.settings import settings
from app.infrastructure.cache.redis_client import (
    get_redis,
    redis_setex,
)


@dataclass(frozen=True)
class OTPResult:
    otp: str


class OTPInvalidError(ValueError):
    pass


class TicketInvalidError(ValueError):
    pass


class OTPTicketService:
    _OTP_CONSUME_LUA = """
local current = redis.call('GET', KEYS[1])
if not current then return nil end
if current ~= ARGV[1] then return 0 end
-- prefer GETDEL when available (Redis >= 6.2)
local ok, val = pcall(redis.call, 'GETDEL', KEYS[1])
if ok then
  return val
end
redis.call('DEL', KEYS[1])
return current
"""

    _TICKET_CONSUME_LUA = """
local current = redis.call('GET', KEYS[1])
if not current then return nil end
if current ~= ARGV[1] then return 0 end
local ok, val = pcall(redis.call, 'GETDEL', KEYS[1])
if ok then
  return val
end
redis.call('DEL', KEYS[1])
return current
"""

    def _otp_key(self, email: str) -> str:
        return f"otp:{email.lower()}"

    def _ticket_key(self, ticket: str) -> str:
        return f"signup_ticket:{ticket}"

    def generate_otp(self) -> str:
        # 6 digits, cryptographically strong
        return f"{secrets.randbelow(1_000_000):06d}"

    async def issue_otp(self, email: str) -> OTPResult:
        otp = self.generate_otp()
        await redis_setex(self._otp_key(email), settings.OTP_TTL_SECONDS, otp.encode("utf-8"))
        return OTPResult(otp=otp)

    async def _consume_otp_value(self, key: str, expected: str) -> bytes | None | int:
        """Atomically read-and-delete the OTP value only when it matches expected.

        Returns:
            bytes: the consumed value when matched and deleted
            0: when value exists but does not match expected
            None: when key is missing/expired
        """
        redis = await get_redis()
        try:
            result = await redis.eval(self._OTP_CONSUME_LUA, 1, key, expected)
            return result
        except ResponseError:
            # Fallback if EVAL is disabled: best-effort match then delete
            value = await redis.get(key)
            if value is None:
                return None
            if value.decode("utf-8") != expected:
                return 0
            await redis.delete(key)
            return value

    async def _consume_ticket_value(self, key: str, expected: str) -> bytes | None | int:
        """Atomically read-and-delete the signup ticket only when it matches expected email."""
        redis = await get_redis()
        try:
            result = await redis.eval(self._TICKET_CONSUME_LUA, 1, key, expected)
            return result
        except ResponseError:
            # Fallback if EVAL is disabled: best-effort match then delete
            value = await redis.get(key)
            if value is None:
                return None
            if value.decode("utf-8") != expected:
                return 0
            await redis.delete(key)
            return value

    async def verify_otp_and_issue_ticket(self, email: str, otp: str) -> str:
        key = self._otp_key(email)
        result = await self._consume_otp_value(key, otp)

        if result is None:
            raise OTPInvalidError("OTP expired or not found")
        if result == 0 or (isinstance(result, bytes) and result.decode("utf-8") != otp):
            raise OTPInvalidError("Invalid OTP")

        ticket = secrets.token_urlsafe(32)
        await redis_setex(
            self._ticket_key(ticket),
            settings.SIGNUP_TICKET_TTL_SECONDS,
            email.lower().encode("utf-8"),
        )
        return ticket

    async def consume_ticket(self, email: str, ticket: str) -> None:
        key = self._ticket_key(ticket)
        expected = email.lower()
        result = await self._consume_ticket_value(key, expected)

        if result is None:
            raise TicketInvalidError("Signup ticket expired or invalid")

        if result == 0 or (isinstance(result, bytes) and result.decode("utf-8") != expected):
            raise TicketInvalidError("Signup ticket does not match email")

        # success path: ticket already deleted atomically
