"""
Notification status endpoint.

Endpoint:
    GET /api/internal/ops/notifications/email

Clean Architecture:
    API layer — calls infrastructure query directly.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from app.infrastructure.notifications.email_metrics import get_email_metrics

router = APIRouter()


class EmailStatusResponse(BaseModel):
    service: str
    status: str
    sent_today: int
    failed_today: int
    note: str
    checked_at: datetime


@router.get(
    "/notifications/email",
    response_model=EmailStatusResponse,
    summary="Email service status and daily send counts",
)
async def get_email_status() -> EmailStatusResponse:
    """
    Email service health and today's send statistics.

    Counters are populated from Redis keys incremented by the email service.
    Counts will remain 0 until increment_email_sent/failed are wired into
    SMTPEmailService send methods.

    Authentication:
        Requires X-Admin-Token header (enforced by parent router).
    """
    metrics = await get_email_metrics()

    return EmailStatusResponse(
        service=metrics.service,
        status=metrics.status,
        sent_today=metrics.sent_today,
        failed_today=metrics.failed_today,
        note="Wire increment_email_sent/failed into SMTPEmailService to populate counts.",
        checked_at=datetime.now(timezone.utc),
    )
