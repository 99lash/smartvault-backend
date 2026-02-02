from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.application.ports.user_repository import UserRepository
from app.domain.models.user import User


class DuplicateEmailError(Exception):
    def __init__(self, email: str):
        super().__init__(f"Email already exists: {email}")
        self.email = email


class PasswordHasher:
    """Port for password hashing; implemented in application/services or infrastructure."""
    def hash(self, raw_password: str) -> str:  # returns encoded hash string
        raise NotImplementedError


@dataclass(frozen=True)
class CreateUserInput:
    email: str
    password: str
    full_name: str | None = None


class CreateUser:
    def __init__(self, repo: UserRepository, hasher: PasswordHasher):
        self._repo = repo
        self._hasher = hasher

    def execute(self, inp: CreateUserInput) -> User:
        email = inp.email.strip().lower()

        # Lightweight validation (leave deeper validation to Pydantic too)
        if "@" not in email or "." not in email.split("@")[-1]:
            raise ValueError("Invalid email format")
        if len(inp.password) < 12:
            raise ValueError("Password must be at least 12 characters")

        existing = self._repo.get_by_email(email)
        if existing is not None:
            raise DuplicateEmailError(email)

        password_hash = self._hasher.hash(inp.password)

        # Create domain User (adapt fields if your domain model differs)
        now = datetime.now(timezone.utc)
        user = User(
            id=str(uuid4()),
            email=email,
            password_hash=password_hash,
            full_name=inp.full_name,
            created_at=now,
        )

        return self._repo.create(user)
