from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.application.ports.user_repository import UserRepository
from app.infrastructure.services.password_reset_service import PasswordResetService
from app.infrastructure.notifications.email_service import EmailService


class PasswordHasher(Protocol):
    def hash(self, raw_password: str) -> str:
        ...


@dataclass(frozen=True)
class RequestPasswordResetInput:
    email: str


class RequestPasswordReset:
    def __init__(
        self,
        repo: UserRepository,
        reset_svc: PasswordResetService,
        email_svc: EmailService,
    ):
        self._repo = repo
        self._reset_svc = reset_svc
        self._email_svc = email_svc

    async def execute(self, inp: RequestPasswordResetInput) -> None:
        email = inp.email.strip().lower()
        user = self._repo.get_by_email(email)
        
        # Always return success to avoid email enumeration
        if user is None:
            return

        token = await self._reset_svc.issue_token(email)
        await self._email_svc.send_password_reset_token(email, token)


@dataclass(frozen=True)
class ConfirmPasswordResetInput:
    token: str
    new_password: str


class ConfirmPasswordReset:
    def __init__(
        self,
        repo: UserRepository,
        reset_svc: PasswordResetService,
        hasher: PasswordHasher,
    ):
        self._repo = repo
        self._reset_svc = reset_svc
        self._hasher = hasher

    async def execute(self, inp: ConfirmPasswordResetInput) -> None:
        email = await self._reset_svc.consume_token(inp.token)
        if email is None:
            raise ValueError("Invalid or expired reset token")

        user = self._repo.get_by_email(email)
        if user is None:
            # Should not happen if token was issued for this email, but be safe
            raise ValueError("User no longer exists")

        if len(inp.new_password) < 12:
            raise ValueError("Password must be at least 12 characters")

        password_hash = self._hasher.hash(inp.new_password)
        self._repo.update_password(user.id, password_hash)
