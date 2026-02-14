"""
Rate limiting dashboard endpoint.

Endpoint:
    GET /api/internal/ops/rate-limits

Clean Architecture:
    API layer — calls infrastructure query directly.
    No application layer needed (read-only aggregation).
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from app.infrastructure.db.queries.rate_limit_metrics import get_rate_limit_metrics

router = APIRouter()


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class ViolatorResponse(BaseModel):
    key: str
    current_count: int
    ttl_seconds: int


class RateLimitsResponse(BaseModel):
    total_active_keys: int
    top_violators: list[ViolatorResponse]
    by_category: dict[str, int]
    checked_at: datetime


# =============================================================================
# ENDPOINT
# =============================================================================

@router.get(
    "/rate-limits",
    response_model=RateLimitsResponse,
    summary="Rate limiting dashboard",
)
async def get_rate_limits_dashboard() -> RateLimitsResponse:
    """
    Active rate limit keys with top violators sorted by request count.

    Scans Redis for rate_limit:* keys written by the RateLimiter.
    Returns top 10 violators and a breakdown by category.

    Authentication:
        Requires X-Admin-Token header (enforced by parent router).
    """
    metrics = await get_rate_limit_metrics()

    return RateLimitsResponse(
        total_active_keys=metrics.total_active_keys,
        top_violators=[
            ViolatorResponse(
                key=v.key,
                current_count=v.current_count,
                ttl_seconds=v.ttl_seconds,
            )
            for v in metrics.top_violators
        ],
        by_category=metrics.by_category,
        checked_at=datetime.now(timezone.utc),
    )
