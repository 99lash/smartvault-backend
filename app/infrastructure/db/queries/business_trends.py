"""
Business trend queries.

Groups user signups and vault provisioning by day over a
configurable window. Produces daily series suitable for charts,
sparklines, and KPI cards in any consumer (TUI, web app).

"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infrastructure.db.models.user_orm import UserORM
from app.infrastructure.db.models.vault_orm import VaultORM


# =============================================================================
# RESULT DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class DailyCount:
    """A single day's count in a trend series."""
    date: str   # YYYY-MM-DD
    count: int


@dataclass(frozen=True)
class TrendSeries:
    """A daily trend series with pre-computed summary statistics."""
    daily: list[DailyCount]
    total: int
    average_per_day: float
    peak_date: str | None       # Date with highest count, None if all zero
    peak_count: int
    change_pct: float | None    # First half vs second half. None if no prior data.


# =============================================================================
# PRIVATE HELPERS
# =============================================================================

def _zero_fill(
    db_rows: list,
    start: date,
    end: date,
) -> list[DailyCount]:
    """
    Walk every day in [start, end] and zero-fill missing dates.

    GROUP BY skips days with no rows. Callers (charts, sparklines)
    need a value for every day in the window.

    Args:
        db_rows: SQLAlchemy rows with .day (str) and .count (int).
        start:   First date of the window (inclusive).
        end:     Last date of the window (inclusive).

    Returns:
        List of DailyCount covering every day in the window.
    """
    counts: dict[str, int] = {
        (row.day.strftime("%Y-%m-%d") if hasattr(row.day, "strftime") else str(row.day)): row.count
        for row in db_rows
    }
    daily: list[DailyCount] = []
    current = start
    while current <= end:
        day_str = current.strftime("%Y-%m-%d")
        daily.append(DailyCount(date=day_str, count=counts.get(day_str, 0)))
        current += timedelta(days=1)
    return daily


def _build_series(daily: list[DailyCount]) -> TrendSeries:
    """
    Compute summary statistics from a zero-filled daily list.

    change_pct compares the sum of the first half of the window
    to the sum of the second half — a simple, dependency-free
    way to detect trend direction without storing history.

    Args:
        daily: Zero-filled list of DailyCount.

    Returns:
        TrendSeries with all fields populated.
    """
    total = sum(d.count for d in daily)
    n = len(daily)
    average_per_day = round(total / n, 1) if n > 0 else 0.0

    peak = max(daily, key=lambda d: d.count, default=None)
    peak_date = peak.date if peak and peak.count > 0 else None
    peak_count = peak.count if peak else 0

    change_pct: float | None = None
    if n >= 2:
        mid = n // 2
        first = sum(d.count for d in daily[:mid])
        second = sum(d.count for d in daily[mid:])
        if first > 0:
            change_pct = round(((second - first) / first) * 100, 1)
        elif second > 0:
            change_pct = 100.0  # went from zero to something

    return TrendSeries(
        daily=daily,
        total=total,
        average_per_day=average_per_day,
        peak_date=peak_date,
        peak_count=peak_count,
        change_pct=change_pct,
    )


def _window(days: int) -> tuple[date, date, datetime]:
    """Return (start_date, end_date, since_datetime) for a day window."""
    now = datetime.now(timezone.utc)
    end = now.date()
    start = end - timedelta(days=days - 1)
    since = datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
    return start, end, since


# =============================================================================
# QUERY FUNCTIONS
# =============================================================================

def get_user_signup_trend(
    db: Session,
    *,
    days: int = 30,
) -> TrendSeries:
    """
    Daily user signup counts over the last N days.

    Groups users.created_at by date. Zero-fills days with no signups
    so the series always has exactly `days` entries.

    Args:
        db:   SQLAlchemy session.
        days: Window size in days (default 30).

    Returns:
        TrendSeries with daily counts and summary statistics.
    """
    start, end, since = _window(days)

    rows = db.execute(
        select(
            func.date(UserORM.created_at).label("day"),
            func.count().label("count"),
        )
        .where(UserORM.created_at >= since)
        .group_by(func.date(UserORM.created_at))
        .order_by(func.date(UserORM.created_at))
    ).all()

    return _build_series(_zero_fill(rows, start, end))


def get_vault_provisioning_trend(
    db: Session,
    *,
    days: int = 30,
) -> TrendSeries:
    """
    Daily vault provisioning counts over the last N days.

    Groups vaults.created_at by date. Zero-fills days with no
    new vaults so the series always has exactly `days` entries.

    Args:
        db:   SQLAlchemy session.
        days: Window size in days (default 30).

    Returns:
        TrendSeries with daily counts and summary statistics.
    """
    start, end, since = _window(days)

    rows = db.execute(
        select(
            func.date(VaultORM.created_at).label("day"),
            func.count().label("count"),
        )
        .where(VaultORM.created_at >= since)
        .group_by(func.date(VaultORM.created_at))
        .order_by(func.date(VaultORM.created_at))
    ).all()

    return _build_series(_zero_fill(rows, start, end))