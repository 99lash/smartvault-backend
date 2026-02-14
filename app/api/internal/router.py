from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.internal.business import activity, overview
from app.api.internal.deps.admin_auth import require_admin_token
from app.api.internal.ops import (
    api_keys,
    audit,
    diagnostics,
    notifications,
    rate_limits,
    sessions,
    summary,
)
from app.api.internal.security import alerts
from app.schemas.admin import AdminPingResponse

internal_router = APIRouter(
    prefix="/internal",
    dependencies=[Depends(require_admin_token)],
    include_in_schema=False,
    tags=["internal"],
)

# =============================================================================
# PING — connectivity check
# =============================================================================

@internal_router.get("/ping", response_model=AdminPingResponse)
def admin_ping() -> AdminPingResponse:
    """Admin API connectivity check."""
    return AdminPingResponse(
        status="ok",
        admin_api="operational",
        version="1.0.0",
    )

# =============================================================================
# BUSINESS endpoints (Slices 2, 5)
# =============================================================================
internal_router.include_router(overview.router,  prefix="/business")
internal_router.include_router(activity.router,  prefix="/business")

# =============================================================================
# SECURITY endpoints (Slice 3)
# =============================================================================
internal_router.include_router(alerts.router, prefix="/security")

# =============================================================================
# OPS — Dashboard & Diagnostics (Slices 1–3 already wired)
# =============================================================================
internal_router.include_router(summary.router,     prefix="/ops")
internal_router.include_router(diagnostics.router, prefix="/ops")

# =============================================================================
# OPS — Rate Limits (Slice 4)
# =============================================================================
internal_router.include_router(rate_limits.router, prefix="/ops")

# =============================================================================
# OPS — Sessions (Slices 5, 6)
# =============================================================================
internal_router.include_router(sessions.router, prefix="/ops")

# =============================================================================
# OPS — Notifications (Slice 7)
# =============================================================================
internal_router.include_router(notifications.router, prefix="/ops")

# =============================================================================
# OPS — Audit Logs (Slice 10)
# =============================================================================
internal_router.include_router(audit.router, prefix="/ops")

# =============================================================================
# OPS — API Keys (Slice 13)
# =============================================================================
internal_router.include_router(api_keys.router, prefix="/ops")
