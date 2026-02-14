"""
Raw database queries for security metrics.

Reads from the access_logs table to detect suspicious patterns
such as repeated failed unlock attempts and PIN lockouts.

Clean Architecture:
    Infrastructure layer — depends on DB models only.
    No domain or application logic here.

Note:
    These are read-only queries — no writes, no side effects.
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
class FailedUnlockStats:
    """Failed vault unlock attempt counts."""
    last_1h: int
    last_24h: int


@dataclass(frozen=True)
class SecuritySummary:
    """Aggregated security event counts for the last 24 hours."""
    failed_unlocks_24h: int
    failed_unlocks_1h: int
    pin_lockouts_24h: int


# =============================================================================
# THRESHOLDS
# Used to determine alert severity
# =============================================================================

FAILED_UNLOCK_WARNING_THRESHOLD_1H = 5    # 5+ failed unlocks/hr → warning
FAILED_UNLOCK_CRITICAL_THRESHOLD_1H = 20  # 20+ failed unlocks/hr → critical
PIN_LOCKOUT_WARNING_THRESHOLD_24H = 3     # 3+ lockouts/day → warning
PIN_LOCKOUT_CRITICAL_THRESHOLD_24H = 10   # 10+ lockouts/day → critical


# =============================================================================
# QUERY FUNCTIONS
# =============================================================================

def get_failed_unlock_stats(db: Session) -> FailedUnlockStats:
    """
    Count failed vault unlock attempts from the access_logs table.

    Args:
        db: SQLAlchemy session.

    Returns:
        FailedUnlockStats with counts for last 1h and 24h windows.
    """
    now = datetime.now(timezone.utc)
    since_1h = now - timedelta(hours=1)
    since_24h = now - timedelta(hours=24)

    last_1h = db.scalar(
        select(func.count())
        .select_from(AccessLogORM)
        .where(
            AccessLogORM.action == "VAULT_UNLOCK_FAILED",
            AccessLogORM.created_at >= since_1h,
        )
    ) or 0

    last_24h = db.scalar(
        select(func.count())
        .select_from(AccessLogORM)
        .where(
            AccessLogORM.action == "VAULT_UNLOCK_FAILED",
            AccessLogORM.created_at >= since_24h,
        )
    ) or 0

    return FailedUnlockStats(last_1h=last_1h, last_24h=last_24h)


def get_pin_lockout_stats(db: Session) -> int:
    """
    Count PIN lockout events in the last 24 hours.

    A lockout is recorded when a vault reaches its max failed
    attempt threshold and is locked out automatically.

    Args:
        db: SQLAlchemy session.

    Returns:
        Count of PIN lockout events in the last 24h.
    """
    now = datetime.now(timezone.utc)
    since_24h = now - timedelta(hours=24)

    return db.scalar(
        select(func.count())
        .select_from(AccessLogORM)
        .where(
            AccessLogORM.action == "VAULT_UNLOCK_FAILED",
            AccessLogORM.metadata_["lockout"].as_boolean() == True,  # noqa: E712
            AccessLogORM.created_at >= since_24h,
        )
    ) or 0


def get_security_summary(db: Session) -> SecuritySummary:
    """
    Full security summary for the last 24 hours.

    Combines failed unlocks and PIN lockout counts
    into a single dataclass for the alerts endpoint.

    Args:
        db: SQLAlchemy session.

    Returns:
        SecuritySummary with all security event counts.
    """
    unlock_stats = get_failed_unlock_stats(db)
    lockouts = get_pin_lockout_stats(db)

    return SecuritySummary(
        failed_unlocks_24h=unlock_stats.last_24h,
        failed_unlocks_1h=unlock_stats.last_1h,
        pin_lockouts_24h=lockouts,
    )