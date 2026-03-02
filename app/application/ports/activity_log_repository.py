from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.models.access_log import AccessLog


class ActivityLogRepository(ABC):
    """
    Port (abstract interface) for activity log persistence.

    Clean Architecture: application layer defines this contract.
    Infrastructure layer (SQLAlchemy) provides the implementation.
    Tests use the in-memory fake.
    """

    @abstractmethod
    def create(self, log: AccessLog) -> AccessLog:
        """
        Persist a new activity log entry.

        Args:
            log: The AccessLog domain object to store.

        Returns:
            The persisted AccessLog (with server-set created_at if applicable).
        """
        raise NotImplementedError

    @abstractmethod
    def list_by_vault(
        self,
        vault_id: str,
        *,
        limit: int = 50,
        before: datetime | None = None,
    ) -> list[AccessLog]:
        """
        Return activity log entries for a vault, newest first.

        Args:
            vault_id: Filter to this vault's events only.
            limit:    Maximum number of entries to return (default 50, max 100).
            before:   Cursor — return only entries older than this timestamp.

        Returns:
            List of AccessLog entries ordered by created_at DESC.
        """
        raise NotImplementedError

    @abstractmethod
    def delete_by_vault_id(self, vault_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def count_recent_by_action(
        self,
        action: str,
        *,
        since: datetime,
    ) -> int:
        """
        Count log entries for a specific action since a given timestamp.

        Used by the alerting system to detect threshold breaches.

        Args:
            action: The action string to filter on (e.g. "VAULT_UNLOCK_FAILED").
            since:  Count only entries created at or after this timestamp.

        Returns:
            Count of matching entries.
        """
        raise NotImplementedError
