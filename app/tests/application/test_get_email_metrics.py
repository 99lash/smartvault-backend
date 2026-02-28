import pytest
import asyncio
from app.application.services.get_email_metrics import GetEmailMetrics
from app.application.ports.email_metrics_service import EmailMetrics

class FakeEmailMetrics:
    service = "email"
    status = "ok"
    sent_today = 42
    failed_today = 2
    note = None

class FakeEmailMetricsService:
    async def get_email_metrics(self) -> EmailMetrics:
        return FakeEmailMetrics()

def test_get_email_metrics():
    use_case = GetEmailMetrics(FakeEmailMetricsService())
    metrics = asyncio.run(use_case.execute())
    assert metrics.service == "email"
    assert metrics.status == "ok"
    assert metrics.sent_today == 42
    assert metrics.failed_today == 2
    assert metrics.note is None
