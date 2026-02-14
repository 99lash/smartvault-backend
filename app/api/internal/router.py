from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.internal.business import activity, overview
from app.api.internal.deps.admin_auth import require_admin_token
from app.api.internal.ops import diagnostics, summary
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
# BUSINESS endpoints
# =============================================================================
internal_router.include_router(
    overview.router,
    prefix="/business",
)

internal_router.include_router(
    activity.router,
    prefix="/business",
)

# =============================================================================
# SECURITY endpoints
# =============================================================================
internal_router.include_router(
    alerts.router,
    prefix="/security",
)

# =============================================================================
# OPS DASHBOARD endpoint
# =============================================================================
internal_router.include_router(
    summary.router,
    prefix="/ops",
)
# =============================================================================
# OPS DIAGNOSTICS endpoints
# =============================================================================
internal_router.include_router(
    diagnostics.router,
    prefix="/ops",
)