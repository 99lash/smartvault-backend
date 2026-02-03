from __future__ import annotations

import secrets
from dataclasses import dataclass

from app.core.settings import settings
from app.infrastructure.cache.redis_client import redis_del, redis_get, redis_setex

@dataclass(frozen=True)
class OTPResult:
    otp: str

class OTPInvalidError(ValueError):
    pass

class TicketInvalidError(ValueError):
    pass

class OTPTicketService:
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

    async def verify_otp_and_issue_ticket(self, email: str, otp: str) -> str:
        key = self._otp_key(email)
        stored = await redis_get(key)
        if stored is None:
            raise OTPInvalidError("OTP expired or not found")

        if stored.decode("utf-8") != otp:
            raise OTPInvalidError("Invalid OTP")

        # one-time: delete OTP once used
        await redis_del(key)

        ticket = secrets.token_urlsafe(32)
        await redis_setex(
            self._ticket_key(ticket),
            settings.SIGNUP_TICKET_TTL_SECONDS,
            email.lower().encode("utf-8"),
        )
        return ticket

    async def consume_ticket(self, email: str, ticket: str) -> None:
        key = self._ticket_key(ticket)
        stored = await redis_get(key)
        if stored is None:
            raise TicketInvalidError("Signup ticket expired or invalid")

        if stored.decode("utf-8") != email.lower():
            raise TicketInvalidError("Signup ticket does not match email")

        # one-time: consume ticket
        await redis_del(key)
