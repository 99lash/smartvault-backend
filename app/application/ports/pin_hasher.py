from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.value_objects.pin import PIN


class PINHasher(ABC):
    """Port for hashing and verifying vault PINs."""

    @abstractmethod
    def hash(self, pin: PIN) -> str:
        """Return a secure hash representation of the PIN."""
        raise NotImplementedError

    @abstractmethod
    def verify(self, pin: PIN, hashed_pin: str) -> bool:
        """Return True if the provided PIN matches the stored hash."""
        raise NotImplementedError
