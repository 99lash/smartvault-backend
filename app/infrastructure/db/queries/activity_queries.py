"""
Raw database queries for recent activity.

Reads from access_logs to provide activity summaries
for the internal ops dashboard.

Clean Architecture:
    Infrastructure layer — depends on DB models only.
    No domain or application logic here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infrastructure.db.models.access_log_orm import AccessLogORM


# =============================================================================
# RESULT DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class RecentActivityEntry:
    """A single recent activity log entry."""
    id: str
    vault_id: str
    user_id: str | None
    action: str
    method: str
    metadata: dict | None
    created_at: datetime


@dataclass(frozen=True)
class ActivitySummary:
    """Aggregated activity counts for a time window."""
    total_events: int
    vault_unlocks: int
    failed_unlocks: int
    pin_operations: int
    member_changes: int
    state_changes: int


# =============================================================================
# QUERY FUNCTIONS
# =============================================================================

def get_recent_activity(
    db: Session,
    *,
    limit: int = 50,
    since_hours: int = 24,
) -> list[RecentActivityEntry]:
    """
    Fetch recent activity log entries across all vaults.

    Args:
        db: SQLAlchemy session.
        limit: Maximum number of entries to return (capped at 100).
        since_hours: Only return entries from the last N hours.

    Returns:
        List of RecentActivityEntry ordered newest first.
    """
    since = datetime.now(timezone.utc) - timedelta(hours=since_hours)

    rows = db.execute(
        select(AccessLogORM)
        .where(AccessLogORM.created_at >= since)
        .order_by(AccessLogORM.created_at.desc())
        .limit(min(limit, 100))
    ).scalars().all()

    return [
        RecentActivityEntry(
            id=row.id,
            vault_id=row.vault_id,
            user_id=row.user_id,
            action=row.action,
            method=row.method,
            metadata=row.metadata_,
            created_at=row.created_at,
        )
        for row in rows
    ]


def get_activity_summary(
    db: Session,
    *,
    since_hours: int = 24,
) -> ActivitySummary:
    """
    Aggregated activity counts for a time window.

    Groups events by action type for the ops dashboard summary.

    Args:
        db: SQLAlchemy session.
        since_hours: Count events from the last N hours.

    Returns:
        ActivitySummary with counts by event category.
    """
    since = datetime.now(timezone.utc) - timedelta(hours=since_hours)

    rows = db.execute(
        select(AccessLogORM.action, func.count().label("count"))
        .where(AccessLogORM.created_at >= since)
        .group_by(AccessLogORM.action)
    ).all()

    counts: dict[str, int] = {row.action: row.count for row in rows}

    total = sum(counts.values())
    vault_unlocks = counts.get("VAULT_UNLOCKED", 0)
    failed_unlocks = counts.get("VAULT_UNLOCK_FAILED", 0)
    pin_operations = counts.get("PIN_SET", 0)
    member_changes = (
        counts.get("MEMBER_ADDED", 0)
        + counts.get("MEMBER_REMOVED", 0)
    )
    state_changes = (
        counts.get("VAULT_STATE_CHANGED", 0)
        + counts.get("UNLOCK_COMMAND_SENT", 0)
    )

    return ActivitySummary(
        total_events=total,
        vault_unlocks=vault_unlocks,
        failed_unlocks=failed_unlocks,
        pin_operations=pin_operations,
        member_changes=member_changes,
        state_changes=state_changes,
    )