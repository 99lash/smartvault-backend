from __future__ import annotations
from abc import ABC, abstractmethod
from app.domain.models.user import User
from typing import Optional

class UserRepository(ABC):
    @abstractmethod
    def save(self, user: User) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        raise NotImplementedError

    @abstractmethod
    def create(self, user: User) -> User:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, user_id: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_ids(self, user_ids: list[str]) -> dict[str, User]:
        raise NotImplementedError

    @abstractmethod
    def update_profile(self, user_id: str, full_name: str | None) -> User | None:
        raise NotImplementedError

    @abstractmethod
    def update_password(self, user_id: str, password_hash: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_provisioning_token(self, token: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    def set_provisioning_token(self, user_id: str, token: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def clear_provisioning_token(self, user_id: str) -> None:
        raise NotImplementedError
