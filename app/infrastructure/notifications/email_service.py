from __future__ import annotations

import logging
from email.message import EmailMessage
from email.utils import formataddr
from typing import Protocol, runtime_checkable

try:
    import aiosmtplib  # type: ignore
except ImportError:  # pragma: no cover - only hit when optional dep missing
    aiosmtplib = None  # type: ignore

log = logging.getLogger(__name__)


@runtime_checkable
class EmailService(Protocol):
    async def send_otp(self, to_email: str, otp: str) -> None:
        ...

    async def send_password_reset_token(self, to_email: str, token: str) -> None:
        ...


class DevEmailService:
    async def send_otp(self, to_email: str, otp: str) -> None:
        # Dev-only backend; mask OTP and log at debug level only.
        masked = otp[:2] + "*" * max(0, len(otp) - 2)
        log.debug("DEV EMAIL: sending masked OTP to %s code=%s", to_email, masked)

    async def send_password_reset_token(self, to_email: str, token: str) -> None:
        # Dev-only backend; mask token and log at debug level only.
        masked = token[:4] + "..." + token[-4:]
        log.debug("DEV EMAIL: sending masked reset token to %s token=%s", to_email, masked)


class SMTPEmailService:
    def __init__(
        self,
        *,
        host: str,
        port: int = 587,
        username: str | None = None,
        password: str | None = None,
        from_email: str,
        from_name: str | None = None,
        use_tls: bool = True,
    ) -> None:
        if aiosmtplib is None:
            raise RuntimeError("aiosmtplib is required for SMTPEmailService")
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.from_name = from_name
        self.use_tls = use_tls

    async def send_otp(self, to_email: str, otp: str) -> None:
        assert aiosmtplib is not None, "SMTP backend not available"

        msg = EmailMessage()
        msg["From"] = (
            formataddr((self.from_name, self.from_email))
            if self.from_name
            else self.from_email
        )
        msg["To"] = to_email
        msg["Subject"] = "Your SmartVault verification code"
        msg.set_content(
            "Use the code below to finish signing in to SmartVault.\n\n"
            f"Code: {otp}\n"
            "If you did not request this code, you can ignore this email."
        )

        await aiosmtplib.send(
            message=msg,
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            start_tls=self.use_tls,
        )

    async def send_password_reset_token(self, to_email: str, token: str) -> None:
        assert aiosmtplib is not None, "SMTP backend not available"

        msg = EmailMessage()
        msg["From"] = (
            formataddr((self.from_name, self.from_email))
            if self.from_name
            else self.from_email
        )
        msg["To"] = to_email
        msg["Subject"] = "Password reset for SmartVault"
        msg.set_content(
            "We received a request to reset your SmartVault password.\n"
            "Use the token below to set a new password:\n\n"
            f"Token: {token}\n\n"
            "This token will expire in 15 minutes.\n"
            "If you did not request a password reset, you can ignore this email."
        )

        await aiosmtplib.send(
            message=msg,
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            start_tls=self.use_tls,
        )
