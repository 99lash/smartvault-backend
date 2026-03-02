from __future__ import annotations

from datetime import datetime

from app.application.ports.activity_log_repository import ActivityLogRepository
from app.domain.models.access_log import AccessLog


class InMemoryActivityLogRepository(ActivityLogRepository):
    """
    In-memory implementation of ActivityLogRepository for use in tests.

    Mirrors the behaviour of the SQLAlchemy implementation without
    requiring a real database connection.
    """

    def __init__(self) -> None:
        self._logs: list[AccessLog] = []

    def clear(self) -> None:
        """Reset state between tests."""
        self._logs.clear()

    # -------------------------------------------------------------------------
    # Port implementation
    # -------------------------------------------------------------------------

    def create(self, log: AccessLog) -> AccessLog:
        self._logs.append(log)
        return log

    def list_by_vault(
        self,
        vault_id: str,
        *,
        limit: int = 50,
        before: datetime | None = None,
    ) -> list[AccessLog]:
        results = [l for l in self._logs if l.vault_id == vault_id]

        if before is not None:
            results = [l for l in results if l.created_at < before]

        # newest first
        results.sort(key=lambda l: l.created_at, reverse=True)
        return results[: min(limit, 100)]

    def count_recent_by_action(
        self,
        action: str,
        *,
        since: datetime,
    ) -> int:
        return sum(
            1 for l in self._logs
            if l.action == action and l.created_at >= since
        )

    def delete_by_vault_id(self, vault_id: str) -> None:
        self._logs = [log for log in self._logs if log.vault_id != vault_id]
