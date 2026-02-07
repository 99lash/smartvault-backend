from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.value_objects.pin_attempt_result import PINAttemptResult


class PINAttemptTracker(ABC):
    """Port for tracking PIN entry attempts and lockout status."""

    @abstractmethod
    async def register_failure(self, vault_id: str) -> tuple[PINAttemptResult, int | None]:
        """
        Record a failed PIN attempt.

        Returns:
            A tuple of (result, attempts_remaining).
            attempts_remaining may be None when unlimited or not tracked.
        """
        raise NotImplementedError

    @abstractmethod
    async def register_success(self, vault_id: str) -> None:
        """Reset counters after a successful PIN entry."""
        raise NotImplementedError

    @abstractmethod
    async def is_locked_out(self, vault_id: str) -> bool:
        """Check whether the vault is currently locked out."""
        raise NotImplementedError
