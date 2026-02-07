from __future__ import annotations

from app.application.ports.pin_hasher import PINHasher
from app.application.services.password_hasher_service import PBKDF2PasswordHasher
from app.domain.value_objects.pin import PIN


class PBKDF2PINHasher(PINHasher):
    """PBKDF2-based PIN hasher using the existing password hasher implementation."""

    def __init__(self, iterations: int = 210_000) -> None:
        self._delegate = PBKDF2PasswordHasher(iterations=iterations)

    def hash(self, pin: PIN) -> str:
        return self._delegate.hash(pin.value)

    def verify(self, pin: PIN, hashed_pin: str) -> bool:
        return self._delegate.verify(pin.value, hashed_pin)
