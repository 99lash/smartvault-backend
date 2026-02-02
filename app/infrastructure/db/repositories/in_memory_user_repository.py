from __future__ import annotations

from typing import Optional

from app.application.ports.user_repository import UserRepository
from app.domain.models.user import User


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self._by_id: dict[str, User] = {}
        self._by_email: dict[str, User] = {}

    def clear(self) -> None:
        self._by_id.clear()
        self._by_email.clear()

    def get_by_email(self, email: str) -> Optional[User]:
        return self._by_email.get(email.strip().lower())

    def create(self, user: User) -> User:
        email = user.email.strip().lower()
        self._by_id[user.id] = user
        self._by_email[email] = user
        return user
