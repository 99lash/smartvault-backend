from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.settings import settings
from app.main import app


def test_email_status_endpoint():
    class FakeEmailMetrics:
        service = "smtp"
        status = "healthy"
        sent_today = 99
        failed_today = 1
        note = None

    class FakeEmailMetricsService:
        async def get_email_metrics(self):
            return FakeEmailMetrics()

    from app.api.internal.ops import notifications as notifications_module
    notifications_module.RedisEmailMetrics = lambda: FakeEmailMetricsService()

    test_token = "test-admin-token"

    with patch.object(settings, "ADMIN_API_TOKEN", test_token):
        client = TestClient(app)
        response = client.get(
            "/api/internal/ops/notifications/email",
            headers={"X-Admin-Token": test_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "smtp"
        assert data["status"] == "healthy"
        assert isinstance(data["sent_today"], int)
        assert isinstance(data["failed_today"], int)

