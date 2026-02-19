"""
Port for retrieving email notification metrics.

Defines the interface for application layer to fetch email status/metrics.
"""
from __future__ import annotations
from typing import Protocol

class EmailMetrics(Protocol):
    service: str
    status: str
    sent_today: int
    failed_today: int
    note: str | None

class EmailMetricsService(Protocol):
    async def get_email_metrics(self) -> EmailMetrics:
        ...
