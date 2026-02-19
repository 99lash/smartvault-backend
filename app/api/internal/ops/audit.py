"""
Audit log endpoint.

Endpoint:
    GET /api/internal/ops/audit

Clean Architecture:
    API layer — calls infrastructure queries directly.
    No application layer needed (read-only, no domain logic).
"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.infrastructure.db.queries.audit_queries import get_audit_logs
from app.api.deps.db import get_db

router = APIRouter()


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class AuditLogItem(BaseModel):
    id: int
    action: str
    target_type: str
    target_id: str | None
    details: dict[str, Any] | None
    ip_address: str | None
    created_at: datetime


class AuditLogsResponse(BaseModel):
    items: list[AuditLogItem]
    total: int
    page: int
    pages: int


# =============================================================================
# ENDPOINT
# =============================================================================

@router.get(
    "/audit",
    response_model=AuditLogsResponse,
    summary="Admin audit logs",
)
def get_audit_logs_endpoint(
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=50, ge=1, le=100, description="Items per page"),
    action: str | None = Query(default=None, description="Filter by action type"),
) -> AuditLogsResponse:
    """
    Paginated admin audit log.

    Records are written by create_audit_log() whenever an admin performs
    a sensitive operation (session revoke, API key create/revoke, etc.).

    Query params:
        page:   Page number (default 1)
        limit:  Items per page (default 50, max 100)
        action: Optional filter — e.g. SESSION_REVOKED, API_KEY_CREATED

    Authentication:
        Requires X-Admin-Token header (enforced by parent router).
    """
    result = get_audit_logs(db, page=page, limit=limit, action=action)

    return AuditLogsResponse(
        items=[
            AuditLogItem(
                id=item.id,
                action=item.action,
                target_type=item.target_type,
                target_id=item.target_id,
                details=item.details,
                ip_address=item.ip_address,
                created_at=item.created_at,
            )
            for item in result.items
        ],
        total=result.total,
        page=result.page,
        pages=result.pages,
    )
