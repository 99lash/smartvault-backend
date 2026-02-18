"""
Security alerts endpoint for the internal admin API.

Detects suspicious activity patterns and returns
structured alerts with severity levels.

Endpoint:
    GET /api/internal/security/alerts

Data sources:
    - access_logs table: failed unlock attempts, PIN lockouts
    - Thresholds: defined in security_metrics.py

Clean Architecture:
    API layer — calls infrastructure queries directly.
    No application layer needed (read-only aggregation).

Alert severity levels:
    ok       → No suspicious activity detected
    warning  → Activity above normal, monitor closely
    critical → Immediate attention required
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.infrastructure.db.queries.security_metrics import (
    FAILED_UNLOCK_CRITICAL_THRESHOLD_1H,
    FAILED_UNLOCK_WARNING_THRESHOLD_1H,
    PIN_LOCKOUT_CRITICAL_THRESHOLD_24H,
    PIN_LOCKOUT_WARNING_THRESHOLD_24H,
    get_security_summary,
)
from app.api.deps.db import get_db

router = APIRouter()

# Type alias for severity levels
AlertSeverity = Literal["low", "medium", "high", "critical"]
AlertStatus = Literal["ok", "warning", "critical"]


# =============================================================================
# RESPONSE SCHEMAS (scoped to this endpoint)
# =============================================================================

class SecurityAlert(BaseModel):
    """A single active security alert."""
    type: str
    severity: AlertSeverity
    message: str
    count: int
    threshold: int
    window: str


class SecuritySummaryResponse(BaseModel):
    """24-hour security event summary."""
    failed_unlocks_1h: int
    failed_unlocks_24h: int
    pin_lockouts_24h: int


class SecurityAlertsResponse(BaseModel):
    """Full security alerts response."""
    generated_at: datetime
    status: AlertStatus
    active_alerts: list[SecurityAlert]
    last_24h: SecuritySummaryResponse


# =============================================================================
# ALERT BUILDING HELPERS
# =============================================================================

def _build_failed_unlock_alert(count_1h: int) -> SecurityAlert | None:
    """
    Build a failed unlock alert if threshold is breached.

    Args:
        count_1h: Number of failed unlock attempts in the last hour.

    Returns:
        SecurityAlert if threshold is breached, None otherwise.
    """
    if count_1h >= FAILED_UNLOCK_CRITICAL_THRESHOLD_1H:
        return SecurityAlert(
            type="failed_unlock_spike",
            severity="critical",
            message=(
                f"{count_1h} failed vault unlock attempts in the last hour. "
                "Possible brute force attack in progress."
            ),
            count=count_1h,
            threshold=FAILED_UNLOCK_CRITICAL_THRESHOLD_1H,
            window="1h",
        )

    if count_1h >= FAILED_UNLOCK_WARNING_THRESHOLD_1H:
        return SecurityAlert(
            type="failed_unlock_spike",
            severity="high",
            message=(
                f"{count_1h} failed vault unlock attempts in the last hour. "
                "Above normal threshold."
            ),
            count=count_1h,
            threshold=FAILED_UNLOCK_WARNING_THRESHOLD_1H,
            window="1h",
        )

    return None


def _build_pin_lockout_alert(lockouts_24h: int) -> SecurityAlert | None:
    """
    Build a PIN lockout alert if threshold is breached.

    Args:
        lockouts_24h: Number of PIN lockout events in the last 24 hours.

    Returns:
        SecurityAlert if threshold is breached, None otherwise.
    """
    if lockouts_24h >= PIN_LOCKOUT_CRITICAL_THRESHOLD_24H:
        return SecurityAlert(
            type="pin_lockout_spike",
            severity="critical",
            message=(
                f"{lockouts_24h} PIN lockout events in the last 24 hours. "
                "Multiple vaults may be under attack."
            ),
            count=lockouts_24h,
            threshold=PIN_LOCKOUT_CRITICAL_THRESHOLD_24H,
            window="24h",
        )

    if lockouts_24h >= PIN_LOCKOUT_WARNING_THRESHOLD_24H:
        return SecurityAlert(
            type="pin_lockout_spike",
            severity="medium",
            message=(
                f"{lockouts_24h} PIN lockout events in the last 24 hours. "
                "Above normal threshold."
            ),
            count=lockouts_24h,
            threshold=PIN_LOCKOUT_WARNING_THRESHOLD_24H,
            window="24h",
        )

    return None


def _determine_status(alerts: list[SecurityAlert]) -> AlertStatus:
    """
    Determine overall status from active alerts.

    Args:
        alerts: List of active alerts.

    Returns:
        "critical" if any critical alert, "warning" if any alerts, "ok" otherwise.
    """
    if not alerts:
        return "ok"

    severities = {a.severity for a in alerts}

    if "critical" in severities:
        return "critical"

    return "warning"


# =============================================================================
# ENDPOINT
# =============================================================================

@router.get(
    "/alerts",
    response_model=SecurityAlertsResponse,
    summary="Security alerts and suspicious activity",
)
def get_security_alerts(
    db: Annotated[Session, Depends(get_db)],
) -> SecurityAlertsResponse:
    """
    Security alerts based on activity log patterns.

    Detects:
    - Failed vault unlock spikes (possible brute force)
    - PIN lockout spikes (multiple vaults under attack)

    Alert thresholds:
    - Failed unlocks: warning ≥5/hr, critical ≥20/hr
    - PIN lockouts:   warning ≥3/24h, critical ≥10/24h

    Authentication:
        Requires X-Admin-Token header (enforced by parent router).
    """
    summary = get_security_summary(db)

    # Build active alerts
    active_alerts: list[SecurityAlert] = []

    unlock_alert = _build_failed_unlock_alert(summary.failed_unlocks_1h)
    if unlock_alert:
        active_alerts.append(unlock_alert)

    lockout_alert = _build_pin_lockout_alert(summary.pin_lockouts_24h)
    if lockout_alert:
        active_alerts.append(lockout_alert)

    return SecurityAlertsResponse(
        generated_at=datetime.now(timezone.utc),
        status=_determine_status(active_alerts),
        active_alerts=active_alerts,
        last_24h=SecuritySummaryResponse(
            failed_unlocks_1h=summary.failed_unlocks_1h,
            failed_unlocks_24h=summary.failed_unlocks_24h,
            pin_lockouts_24h=summary.pin_lockouts_24h,
        ),
    )