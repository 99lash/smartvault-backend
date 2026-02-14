from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.application.ports.activity_log_repository import ActivityLogRepository
from app.domain.models.access_log import AccessLog, ActivityAction, ActivityMethod


@dataclass
class LogActivityInput:
    """
    Input for the LogActivity use case.

    Attributes:
        vault_id:  The vault this event belongs to.
        action:    What happened (e.g. VAULT_UNLOCKED, PIN_SET).
        method:    How it was triggered (e.g. PIN, SYSTEM).
        user_id:   Who triggered it. None for system-triggered events.
        metadata:  Optional extra context dict (e.g. role, previous status).
    """
    vault_id: str
    action: ActivityAction
    method: ActivityMethod
    user_id: str | None = None
    metadata: dict | None = None


class LogActivity:
    """
    Use case: persist one activity log entry for a vault event.

    Callers (other use cases, endpoints) pass a LogActivityInput.
    This use case owns ID generation and timestamping so callers
    stay free of those concerns.

    Clean Architecture:
        Application layer — depends only on the port interface,
        never on SQLAlchemy or any infrastructure detail.
    """

    def __init__(self, repo: ActivityLogRepository) -> None:
        self._repo = repo

    def execute(self, input: LogActivityInput) -> AccessLog:
        """
        Create and persist an activity log entry.

        Args:
            input: LogActivityInput describing the event.

        Returns:
            The persisted AccessLog domain object.
        """
        log = AccessLog(
            id=f"log_{uuid4()}",
            vault_id=input.vault_id,
            user_id=input.user_id,
            action=input.action,
            method=input.method,
            metadata=input.metadata,
            created_at=datetime.now(timezone.utc),
        )
        return self._repo.create(log)