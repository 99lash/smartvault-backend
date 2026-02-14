"""
Admin audit log queries.

Follows activity_queries.py pattern:
- Frozen dataclass result types
- SQLAlchemy Core selects (select(), func.count())
- Pagination via offset/limit
- No domain model mapping (infrastructure-only)

Clean Architecture:
    Infrastructure layer — database queries only.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infrastructure.db.models.admin_audit_orm import AdminAuditORM


# =============================================================================
# RESULT DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class AuditLogEntry:
    id: int
    action: str
    target_type: str
    target_id: str | None
    details: dict[str, Any] | None
    ip_address: str | None
    created_at: datetime


@dataclass(frozen=True)
class PaginatedAuditLogs:
    items: list[AuditLogEntry]
    total: int
    page: int
    pages: int


# =============================================================================
# HELPERS
# =============================================================================

def _to_entry(row: AdminAuditORM) -> AuditLogEntry:
    return AuditLogEntry(
        id=row.id,
        action=row.action,
        target_type=row.target_type,
        target_id=row.target_id,
        details=row.details,
        ip_address=row.ip_address,
        created_at=row.created_at,
    )


# =============================================================================
# QUERY FUNCTIONS
# =============================================================================

def get_audit_logs(
    db: Session,
    *,
    page: int = 1,
    limit: int = 50,
    action: str | None = None,
) -> PaginatedAuditLogs:
    """
    Get paginated audit logs with optional action filter.

    Args:
        db:     SQLAlchemy session.
        page:   1-indexed page number.
        limit:  Items per page (capped at 100).
        action: Optional exact-match filter on action column.

    Returns:
        PaginatedAuditLogs with items and pagination metadata.
    """
    limit = min(limit, 100)

    base_stmt  = select(AdminAuditORM)
    count_stmt = select(func.count()).select_from(AdminAuditORM)

    if action:
        base_stmt  = base_stmt.where(AdminAuditORM.action == action)
        count_stmt = count_stmt.where(AdminAuditORM.action == action)

    total = db.scalar(count_stmt) or 0
    pages = max(1, (total + limit - 1) // limit) if total > 0 else 0

    rows = db.scalars(
        base_stmt
        .order_by(AdminAuditORM.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()

    return PaginatedAuditLogs(
        items=[_to_entry(r) for r in rows],
        total=total,
        page=page,
        pages=pages,
    )


def create_audit_log(
    db: Session,
    *,
    action: str,
    target_type: str,
    target_id: str | None = None,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AuditLogEntry:
    """
    Persist a new audit log entry.

    Args:
        db:          SQLAlchemy session.
        action:      Action type (e.g. SESSION_REVOKED, API_KEY_CREATED).
        target_type: Object type (e.g. user, api_key).
        target_id:   ID of the target object.
        details:     Additional JSON context.
        ip_address:  Client IP (optional).

    Returns:
        The persisted AuditLogEntry.
    """
    row = AdminAuditORM(
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_entry(row)
