from __future__ import annotations

import logging

log = logging.getLogger(__name__)

class EmailService:
    async def send_otp(self, to_email: str, otp: str) -> None:
        raise NotImplementedError

class DevEmailService(EmailService):
    async def send_otp(self, to_email: str, otp: str) -> None:
        # Do not log OTP in production; this is dev-only.
        log.info("DEV EMAIL: sending OTP to %s", to_email)
        log.info("DEV EMAIL OTP: %s", otp)
