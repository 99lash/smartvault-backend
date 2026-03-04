from __future__ import annotations

from abc import ABC, abstractmethod


class ProvisioningTokenStore(ABC):
    @abstractmethod
    async def set(self, token: str, user_id: str, ttl_seconds: int) -> bool:
        """Store token → user_id with TTL. Returns True if set, False if key already exists."""
        raise NotImplementedError

    @abstractmethod
    async def get(self, token: str) -> str | None:
        """Return user_id for token, or None if not found/expired."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, token: str) -> None:
        raise NotImplementedError
