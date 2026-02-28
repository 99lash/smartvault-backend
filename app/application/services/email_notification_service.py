"""
Email notification service with metrics tracking.

Wraps an EmailService implementation and records send/failure metrics.

Clean Architecture:
    Application layer service — orchestrates email sending with observability.
    Depends on EmailService port (not concrete implementation).
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable, Awaitable

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
        on_sent: Callback for successful email send (e.g. metrics increment)
        on_failed: Callback for failed email send (e.g. metrics increment)
    """

    def __init__(
        self,
        email_service: EmailService,
        on_sent: Callable[[], Awaitable[None]] | None = None,
        on_failed: Callable[[], Awaitable[None]] | None = None,
    ):
        self._email_service = email_service
        self._on_sent = on_sent
        self._on_failed = on_failed

    async def _safe_callback(self, callback: Callable[[], Awaitable[None]] | None) -> None:
        """Execute callback safely without raising exceptions."""
        if not callback:
            return
        try:
            await callback()
        except Exception:
            # Metrics failure should not block the application flow
            log.exception("Failed to execute email notification callback")

    async def send_otp(self, to_email: str, otp: str) -> None:
        """
        Send OTP email and track metrics.
        
        Args:
            to_email: Recipient email address
            otp: One-time password code
            
        Raises:
            Exception: If email sending fails (metrics tracked before re-raise)
        """
        try:
            await self._email_service.send_otp(to_email, otp)
            await self._safe_callback(self._on_sent)
        except Exception as e:
            await self._safe_callback(self._on_failed)
            # Remove PII (email) from log
            log.error("Failed to send OTP email", extra={"error": str(e)})
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
        try:
            await self._email_service.send_password_reset_token(to_email, token)
            await self._safe_callback(self._on_sent)
        except Exception as e:
            await self._safe_callback(self._on_failed)
            # Remove PII (email) from log
            log.error("Failed to send password reset email", extra={"error": str(e)})
            raise
