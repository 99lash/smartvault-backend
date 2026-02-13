from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infrastructure.db.models.user_orm import UserORM
from app.infrastructure.db.models.vault_authorization_orm import VaultAuthorizationORM
from app.infrastructure.db.models.vault_orm import VaultORM


# =============================================================================
# RESULT DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class UserMetrics:
    """Aggregated user counts."""
    total: int
    new_today: int
    new_this_week: int


@dataclass(frozen=True)
class VaultMetrics:
    """Aggregated vault counts."""
    total: int
    with_pin: int
    by_status: dict[str, int]


@dataclass(frozen=True)
class MemberMetrics:
    """Aggregated vault authorization counts."""
    total_authorizations: int
    by_role: dict[str, int]


# =============================================================================
# QUERY FUNCTIONS
# =============================================================================

def get_user_metrics(db: Session) -> UserMetrics:
    """
    Query aggregated user metrics from the database.

    Args:
        db: SQLAlchemy session.

    Returns:
        UserMetrics with total, new_today, new_this_week counts.
    """
    now = datetime.now(timezone.utc)
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_week = start_of_today - timedelta(days=now.weekday())

    total = db.scalar(
        select(func.count()).select_from(UserORM)
    ) or 0

    new_today = db.scalar(
        select(func.count())
        .select_from(UserORM)
        .where(UserORM.created_at >= start_of_today)
    ) or 0

    new_this_week = db.scalar(
        select(func.count())
        .select_from(UserORM)
        .where(UserORM.created_at >= start_of_week)
    ) or 0

    return UserMetrics(
        total=total,
        new_today=new_today,
        new_this_week=new_this_week,
    )


def get_vault_metrics(db: Session) -> VaultMetrics:
    """
    Query aggregated vault metrics from the database.

    Args:
        db: SQLAlchemy session.

    Returns:
        VaultMetrics with total, with_pin, and by_status breakdown.
    """
    total = db.scalar(
        select(func.count()).select_from(VaultORM)
    ) or 0

    with_pin = db.scalar(
        select(func.count())
        .select_from(VaultORM)
        .where(VaultORM.pin_hash.is_not(None))
    ) or 0

    # Group by status
    status_rows = db.execute(
        select(VaultORM.status, func.count().label("count"))
        .group_by(VaultORM.status)
    ).all()

    by_status = {row.status: row.count for row in status_rows}

    return VaultMetrics(
        total=total,
        with_pin=with_pin,
        by_status=by_status,
    )


def get_member_metrics(db: Session) -> MemberMetrics:
    """
    Query aggregated vault member metrics from the database.

    Args:
        db: SQLAlchemy session.

    Returns:
        MemberMetrics with total authorizations and by_role breakdown.
    """
    total = db.scalar(
        select(func.count()).select_from(VaultAuthorizationORM)
    ) or 0

    # Group by role
    role_rows = db.execute(
        select(
            VaultAuthorizationORM.role,
            func.count().label("count")
        )
        .group_by(VaultAuthorizationORM.role)
    ).all()

    by_role = {row.role: row.count for row in role_rows}

    return MemberMetrics(
        total_authorizations=total,
        by_role=by_role,
    )