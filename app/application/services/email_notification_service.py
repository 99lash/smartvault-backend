"""
Email notification service with metrics tracking.

Wraps an EmailService implementation and records send/failure metrics.

Clean Architecture:
    Application layer service — orchestrates email sending with observability.
    Depends on EmailService port (not concrete implementation).
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.application.ports.email_service import EmailService

log = logging.getLogger(__name__)


class EmailNotificationService:
    """
    Application service for sending emails with metrics tracking.
    
    Wraps the underlying email service implementation and tracks
    success/failure counts in Redis for observability.
    
    Args:
        email_service: Infrastructure implementation (SMTP, dev, etc.)
    """

    def __init__(self, email_service: EmailService):
        self._email_service = email_service

    async def send_otp(self, to_email: str, otp: str) -> None:
        """
        Send OTP email and track metrics.
        
        Args:
            to_email: Recipient email address
            otp: One-time password code
            
        Raises:
            Exception: If email sending fails (metrics tracked before re-raise)
        """
        from app.infrastructure.notifications.email_metrics import (
            increment_email_sent,
            increment_email_failed,
        )

        try:
            await self._email_service.send_otp(to_email, otp)
            await increment_email_sent()
        except Exception as e:
            await increment_email_failed()
            log.error("Failed to send OTP email", extra={"error": str(e), "to": to_email})
            raise

    async def send_password_reset_token(self, to_email: str, token: str) -> None:
        """
        Send password reset token email and track metrics.
        
        Args:
            to_email: Recipient email address
            token: Password reset token
            
        Raises:
            Exception: If email sending fails (metrics tracked before re-raise)
        """
        from app.infrastructure.notifications.email_metrics import (
            increment_email_sent,
            increment_email_failed,
        )

        try:
            await self._email_service.send_password_reset_token(to_email, token)
            await increment_email_sent()
        except Exception as e:
            await increment_email_failed()
            log.error("Failed to send password reset email", extra={"error": str(e), "to": to_email})
            raise
