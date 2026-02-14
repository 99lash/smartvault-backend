"""
Session management endpoints.

Endpoints:
    GET    /api/internal/ops/sessions/stats
    DELETE /api/internal/ops/sessions/{user_id}

Clean Architecture:
    API layer — calls infrastructure service directly.
    Uses sync session_metrics (matches refresh_token_store.py pattern).
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from app.infrastructure.services.session_metrics import (
    get_session_metrics,
    revoke_user_sessions,
)

router = APIRouter()


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class TopUserResponse(BaseModel):
    user_id: str
    token_count: int


class SessionStatsResponse(BaseModel):
    total_active_tokens: int
    top_users: list[TopUserResponse]
    checked_at: datetime


class RevokeSessionsResponse(BaseModel):
    user_id: str
    sessions_revoked: int


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get(
    "/sessions/stats",
    response_model=SessionStatsResponse,
    summary="Refresh token session statistics",
)
def get_session_stats() -> SessionStatsResponse:
    """
    Active refresh token statistics.

    Scans Redis for refresh:* keys to report total active sessions
    and the users with the most concurrent sessions (top 10).

    Authentication:
        Requires X-Admin-Token header (enforced by parent router).
    """
    metrics = get_session_metrics()

    return SessionStatsResponse(
        total_active_tokens=metrics.total_active_tokens,
        top_users=[
            TopUserResponse(
                user_id=u["user_id"],
                token_count=u["token_count"],
            )
            for u in metrics.top_users
        ],
        checked_at=datetime.now(timezone.utc),
    )


@router.delete(
    "/sessions/{user_id}",
    response_model=RevokeSessionsResponse,
    summary="Revoke all sessions for a user",
)
def revoke_all_user_sessions(user_id: str) -> RevokeSessionsResponse:
    """
    Force-logout a user by revoking all their refresh tokens.

    Scans Redis for refresh:* keys belonging to the user and deletes them.
    The user will need to re-authenticate on all devices.

    Use for: compromised accounts, suspicious activity, admin security action.

    Args:
        user_id: ID of the user whose sessions to revoke.

    Authentication:
        Requires X-Admin-Token header (enforced by parent router).
    """
    revoked = revoke_user_sessions(user_id)

    return RevokeSessionsResponse(
        user_id=user_id,
        sessions_revoked=revoked,
    )
