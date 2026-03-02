from __future__ import annotations

from dataclasses import replace
from typing import Optional

from app.application.ports.user_repository import UserRepository
from app.domain.models.user import User


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self._by_id: dict[str, User] = {}
        self._by_email: dict[str, User] = {}

    def save(self, user: User) -> None:
        email = user.email.strip().lower()
        self._by_id[user.id] = user
        self._by_email[email] = user
    
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
    
    def get_by_id(self, user_id: str) -> User | None:
        return self._by_id.get(user_id)

    def update_profile(self, user_id: str, full_name: str | None) -> User | None:
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        # Create a copy with the new name (since User is likely frozen/immutable)
        updated_user = replace(user, full_name=full_name)
        self.save(updated_user)
        return updated_user

    def update_password(self, user_id: str, password_hash: str) -> User | None:
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        updated_user = replace(user, password_hash=password_hash)
        self.save(updated_user)
        return updated_user

    def get_by_ids(self, user_ids: list[str]) -> dict[str, User]:
        return {uid: user for uid, user in self._by_id.items() if uid in user_ids}

    def get_by_provisioning_token(self, token: str) -> User | None:
        for user in self._by_id.values():
            if user.provisioning_token == token:
                return user
        return None

    def set_provisioning_token(self, user_id: str, token: str) -> None:
        user = self._by_id.get(user_id)
        if user is None:
            raise ValueError(f"User {user_id} not found")
        self.save(replace(user, provisioning_token=token))

    def clear_provisioning_token(self, user_id: str) -> None:
        user = self._by_id.get(user_id)
        if user is None:
            raise ValueError(f"User {user_id} not found")
        self.save(replace(user, provisioning_token=None))
