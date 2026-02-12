from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from app.infrastructure.notifications.email_service import EmailService


@dataclass
class SentOTP:
    to_email: str
    otp: str


@dataclass
class SentToken:
    to_email: str
    token: str


class CaptureEmailService(EmailService):
    """
    Test double that captures OTPs and tokens instead of sending real email.
    """
    def __init__(self) -> None:
        self.sent: list[SentOTP] = []
        self.sent_tokens: list[SentToken] = []
        self._latest_otp_by_email: Dict[str, str] = {}
        self._latest_token_by_email: Dict[str, str] = {}

    async def send_otp(self, to_email: str, otp: str) -> None:
        self.sent.append(SentOTP(to_email=to_email, otp=otp))
        self._latest_otp_by_email[to_email] = otp

    async def send_password_reset_token(self, to_email: str, token: str) -> None:
        self.sent_tokens.append(SentToken(to_email=to_email, token=token))
        self._latest_token_by_email[to_email] = token

    def latest_otp_for(self, email: str) -> Optional[str]:
        return self._latest_otp_by_email.get(email)

    def latest_token_for(self, email: str) -> Optional[str]:
        return self._latest_token_by_email.get(email)

    def clear(self) -> None:
        self.sent.clear()
        self.sent_tokens.clear()
        self._latest_otp_by_email.clear()
        self._latest_token_by_email.clear()
