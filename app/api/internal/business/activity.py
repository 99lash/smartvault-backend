from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.infrastructure.db.queries.activity_queries import (
    get_activity_summary,
    get_recent_activity,
)
from app.infrastructure.db.session import get_db

router = APIRouter()


# =============================================================================
# RESPONSE SCHEMAS (scoped to this endpoint)
# =============================================================================

class ActivityEntry(BaseModel):
    """A single activity log entry."""
    id: str
    vault_id: str
    user_id: str | None
    action: str
    method: str
    metadata: dict | None
    created_at: datetime


class ActivitySummaryResponse(BaseModel):
    """Aggregated activity counts."""
    total_events: int
    vault_unlocks: int
    failed_unlocks: int
    pin_operations: int
    member_changes: int
    state_changes: int


class ActivityResponse(BaseModel):
    """Full activity response with entries and summary."""
    generated_at: datetime
    period_hours: int
    summary: ActivitySummaryResponse
    entries: list[ActivityEntry]


# =============================================================================
# ENDPOINT
# =============================================================================

@router.get(
    "/activity",
    response_model=ActivityResponse,
    summary="Recent activity log",
)
def get_activity(
    db: Annotated[Session, Depends(get_db)],
    hours: int = Query(default=24, ge=1, le=168, description="Activity window in hours (1-168)"),
    limit: int = Query(default=50, ge=1, le=100, description="Max entries to return"),
) -> ActivityResponse:
    """
    Recent activity across all vaults.

    Returns the latest events from the access_logs table
    with an aggregated summary broken down by event type.

    Query params:
        hours:  Time window in hours (default 24, max 168 = 7 days)
        limit:  Max entries to return (default 50, max 100)

    Authentication:
        Requires X-Admin-Token header (enforced by parent router).
    """
    entries = get_recent_activity(db, limit=limit, since_hours=hours)
    summary = get_activity_summary(db, since_hours=hours)

    return ActivityResponse(
        generated_at=datetime.now(timezone.utc),
        period_hours=hours,
        summary=ActivitySummaryResponse(
            total_events=summary.total_events,
            vault_unlocks=summary.vault_unlocks,
            failed_unlocks=summary.failed_unlocks,
            pin_operations=summary.pin_operations,
            member_changes=summary.member_changes,
            state_changes=summary.state_changes,
        ),
        entries=[
            ActivityEntry(
                id=e.id,
                vault_id=e.vault_id,
                user_id=e.user_id,
                action=e.action,
                method=e.method,
                metadata=e.metadata,
                created_at=e.created_at,
            )
            for e in entries
        ],
    )