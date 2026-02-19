"""
Email service port (interface).

Defines the contract for sending emails without specifying implementation.

Clean Architecture:
    Application layer port — defines interface for infrastructure adapters.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmailService(Protocol):
    """Port for email sending operations."""

    async def send_otp(self, to_email: str, otp: str) -> None:
        """Send OTP verification code email."""
        ...

    async def send_password_reset_token(self, to_email: str, token: str) -> None:
        """Send password reset token email."""
        ...
