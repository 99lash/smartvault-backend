from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.infrastructure.db.queries.activity_queries import get_activity_summary
from app.infrastructure.db.queries.business_metrics import (
    get_member_metrics,
    get_user_metrics,
    get_vault_metrics,
)
from app.infrastructure.db.queries.security_metrics import (
    FAILED_UNLOCK_CRITICAL_THRESHOLD_1H,
    FAILED_UNLOCK_WARNING_THRESHOLD_1H,
    PIN_LOCKOUT_CRITICAL_THRESHOLD_24H,
    PIN_LOCKOUT_WARNING_THRESHOLD_24H,
    get_security_summary,
)
from app.infrastructure.db.session import get_db

router = APIRouter()

# Type aliases
SystemStatus = Literal["ok", "warning", "critical"]


# =============================================================================
# RESPONSE SCHEMAS (scoped to this endpoint)
# =============================================================================

class OpsUserSummary(BaseModel):
    total: int
    new_today: int
    new_this_week: int


class OpsVaultSummary(BaseModel):
    total: int
    with_pin: int
    by_status: dict[str, int]


class OpsMemberSummary(BaseModel):
    total_authorizations: int
    by_role: dict[str, int]


class OpsBusinessSummary(BaseModel):
    users: OpsUserSummary
    vaults: OpsVaultSummary
    members: OpsMemberSummary


class OpsSecuritySummary(BaseModel):
    status: SystemStatus
    failed_unlocks_1h: int
    failed_unlocks_24h: int
    pin_lockouts_24h: int
    alert_count: int


class OpsActivitySummary(BaseModel):
    period_hours: int
    total_events: int
    vault_unlocks: int
    failed_unlocks: int
    pin_operations: int
    member_changes: int
    state_changes: int


class OpsSummaryResponse(BaseModel):
    """
    Complete operational summary for the admin dashboard.

    Combines business metrics, security status, and activity
    into a single response suitable for a dashboard homepage.
    """
    generated_at: datetime
    overall_status: SystemStatus
    business: OpsBusinessSummary
    security: OpsSecuritySummary
    activity: OpsActivitySummary


# =============================================================================
# HELPERS
# =============================================================================

def _security_status(failed_1h: int, lockouts_24h: int) -> SystemStatus:
    """Derive security status from raw counts."""
    if (
        failed_1h >= FAILED_UNLOCK_CRITICAL_THRESHOLD_1H
        or lockouts_24h >= PIN_LOCKOUT_CRITICAL_THRESHOLD_24H
    ):
        return "critical"

    if (
        failed_1h >= FAILED_UNLOCK_WARNING_THRESHOLD_1H
        or lockouts_24h >= PIN_LOCKOUT_WARNING_THRESHOLD_24H
    ):
        return "warning"

    return "ok"


def _alert_count(failed_1h: int, lockouts_24h: int) -> int:
    """Count how many alert thresholds are currently breached."""
    count = 0
    if failed_1h >= FAILED_UNLOCK_WARNING_THRESHOLD_1H:
        count += 1
    if lockouts_24h >= PIN_LOCKOUT_WARNING_THRESHOLD_24H:
        count += 1
    return count


# =============================================================================
# ENDPOINT
# =============================================================================

@router.get(
    "/summary",
    response_model=OpsSummaryResponse,
    summary="Complete ops dashboard summary",
)
def get_ops_summary(
    db: Annotated[Session, Depends(get_db)],
) -> OpsSummaryResponse:
    """
    Complete operational summary for the admin dashboard.

    Combines:
    - Business metrics (users, vaults, members)
    - Security status (failed unlocks, PIN lockouts)
    - Activity summary (last 24h event counts)

    Overall status:
        ok       → No security alerts active
        warning  → At least one warning threshold breached
        critical → At least one critical threshold breached

    Authentication:
        Requires X-Admin-Token header (enforced by parent router).
    """
    # Gather all data in parallel logical groups
    user_metrics = get_user_metrics(db)
    vault_metrics = get_vault_metrics(db)
    member_metrics = get_member_metrics(db)
    security = get_security_summary(db)
    activity = get_activity_summary(db, since_hours=24)

    sec_status = _security_status(
        failed_1h=security.failed_unlocks_1h,
        lockouts_24h=security.pin_lockouts_24h,
    )

    return OpsSummaryResponse(
        generated_at=datetime.now(timezone.utc),
        overall_status=sec_status,
        business=OpsBusinessSummary(
            users=OpsUserSummary(
                total=user_metrics.total,
                new_today=user_metrics.new_today,
                new_this_week=user_metrics.new_this_week,
            ),
            vaults=OpsVaultSummary(
                total=vault_metrics.total,
                with_pin=vault_metrics.with_pin,
                by_status=vault_metrics.by_status,
            ),
            members=OpsMemberSummary(
                total_authorizations=member_metrics.total_authorizations,
                by_role=member_metrics.by_role,
            ),
        ),
        security=OpsSecuritySummary(
            status=sec_status,
            failed_unlocks_1h=security.failed_unlocks_1h,
            failed_unlocks_24h=security.failed_unlocks_24h,
            pin_lockouts_24h=security.pin_lockouts_24h,
            alert_count=_alert_count(
                failed_1h=security.failed_unlocks_1h,
                lockouts_24h=security.pin_lockouts_24h,
            ),
        ),
        activity=OpsActivitySummary(
            period_hours=24,
            total_events=activity.total_events,
            vault_unlocks=activity.vault_unlocks,
            failed_unlocks=activity.failed_unlocks,
            pin_operations=activity.pin_operations,
            member_changes=activity.member_changes,
            state_changes=activity.state_changes,
        ),
    )