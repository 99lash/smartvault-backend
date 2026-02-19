"""
Business trend endpoint.

Returns daily time-series data for user signups and vault
provisioning over a configurable window (7–90 days).

Designed to serve all consumers with one response:
    - TUI: reads daily[] for sparklines, summary fields for KPI labels
    - Web app: reads daily[] for charts, summary fields for KPI cards

"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.infrastructure.db.queries.business_trends import (
    get_user_signup_trend,
    get_vault_provisioning_trend,
)
from app.api.deps.db import get_db

router = APIRouter()


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class DailyCountResponse(BaseModel):
    """A single day's count."""
    date: str   # YYYY-MM-DD
    count: int


class TrendSeriesResponse(BaseModel):
    """A trend series with daily data and summary statistics."""
    daily: list[DailyCountResponse]
    total: int
    average_per_day: float
    peak_date: str | None
    peak_count: int
    change_pct: float | None


class BusinessTrendsResponse(BaseModel):
    """User signup and vault provisioning trends."""
    generated_at: datetime
    period_days: int
    period_start: str   # YYYY-MM-DD — first day in both series
    period_end: str     # YYYY-MM-DD — last day in both series
    user_signups: TrendSeriesResponse
    vault_provisioning: TrendSeriesResponse


# =============================================================================
# ENDPOINT
# =============================================================================

@router.get(
    "/trends",
    response_model=BusinessTrendsResponse,
    summary="User signup and vault provisioning trends",
)
def get_business_trends(
    db: Annotated[Session, Depends(get_db)],
    days: int = Query(
        default=30,
        ge=7,
        le=90,
        description="Window size in days (7, 14, 30, or 90)",
    ),
) -> BusinessTrendsResponse:
    """
    Daily time-series data for user signups and vault provisioning.

    Returns one entry per day for the requested window with zero-filled
    gaps, so consumers always receive exactly `days` data points per series.

    Summary fields (total, average_per_day, peak_date, peak_count,
    change_pct) are pre-computed — consumers do not need to aggregate.

    change_pct compares the first half of the window to the second half:
        positive → growth, negative → decline, null → no prior data.

    Query params:
        days: Window size in days (default 30, min 7, max 90).

    Authentication:
        Requires X-Admin-Token header (enforced by parent router).
    """
    user_trend = get_user_signup_trend(db, days=days)
    vault_trend = get_vault_provisioning_trend(db, days=days)

    # Both series share the same date range — read period from user series
    period_start = user_trend.daily[0].date if user_trend.daily else ""
    period_end = user_trend.daily[-1].date if user_trend.daily else ""

    def _map_series(series) -> TrendSeriesResponse:
        return TrendSeriesResponse(
            daily=[
                DailyCountResponse(date=d.date, count=d.count)
                for d in series.daily
            ],
            total=series.total,
            average_per_day=series.average_per_day,
            peak_date=series.peak_date,
            peak_count=series.peak_count,
            change_pct=series.change_pct,
        )

    return BusinessTrendsResponse(
        generated_at=datetime.now(timezone.utc),
        period_days=days,
        period_start=period_start,
        period_end=period_end,
        user_signups=_map_series(user_trend),
        vault_provisioning=_map_series(vault_trend),
    )