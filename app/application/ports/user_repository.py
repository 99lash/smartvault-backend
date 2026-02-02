from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.models.user import User


class UserRepository(ABC):
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        raise NotImplementedError

    @abstractmethod
    def create(self, user: User) -> User:
        raise NotImplementedError
