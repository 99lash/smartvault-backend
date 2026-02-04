from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from app.infrastructure.notifications.email_service import EmailService


@dataclass
class SentOTP:
    to_email: str
    otp: str


class CaptureEmailService(EmailService):
    """
    Test double that captures OTPs instead of sending real email.
    """
    def __init__(self) -> None:
        self.sent: list[SentOTP] = []
        self._latest_by_email: Dict[str, str] = {}

    async def send_otp(self, to_email: str, otp: str) -> None:
        self.sent.append(SentOTP(to_email=to_email, otp=otp))
        self._latest_by_email[to_email] = otp

    def latest_otp_for(self, email: str) -> Optional[str]:
        return self._latest_by_email.get(email)

    def clear(self) -> None:
        self.sent.clear()
        self._latest_by_email.clear()
