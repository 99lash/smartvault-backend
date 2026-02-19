"""
Application service for retrieving email notification metrics.
Depends on EmailMetricsService port.
"""
from __future__ import annotations
from app.application.ports.email_metrics_service import EmailMetricsService, EmailMetrics

class GetEmailMetrics:
    def __init__(self, metrics_service: EmailMetricsService):
        self._metrics_service = metrics_service

    async def execute(self) -> EmailMetrics:
        return await self._metrics_service.get_email_metrics()
