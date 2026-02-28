"""
Tests for email notification status endpoint.

Patch target: app.api.internal.ops.notifications.get_email_metrics
(where it's used, not where it's defined)
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.core.settings import settings
from app.infrastructure.notifications.email_metrics import EmailMetrics

VALID_TOKEN = "test-admin-token-abc123"

_PATCH_TARGET = "app.api.internal.ops.notifications.get_email_metrics"


@pytest.fixture
def admin_client(app, vault_repo, vault_auth_repo, user_repo, rate_limiter):
    from fastapi.testclient import TestClient
    with patch.object(settings, "ADMIN_API_TOKEN", VALID_TOKEN):
        with TestClient(app) as c:
            yield c


def test_email_status_returns_metrics(admin_client):
    """Email status returns service status and send counts."""
    mock = AsyncMock(return_value=EmailMetrics(
        service="smtp",
        status="healthy",
        sent_today=42,
        failed_today=1,
        note=None,
    ))

    with patch(_PATCH_TARGET, mock):
        response = admin_client.get(
            "/api/internal/ops/notifications/email",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "smtp"
    assert data["status"] == "healthy"
    assert data["sent_today"] == 42
    assert data["failed_today"] == 1
    assert "checked_at" in data
    assert "note" in data


def test_email_status_returns_zeros_when_no_sends(admin_client):
    """Email status returns 0 counts before any emails are sent."""
    mock = AsyncMock(return_value=EmailMetrics(
        service="smtp", status="healthy", sent_today=0, failed_today=0, note=None
    ))

    with patch(_PATCH_TARGET, mock):
        response = admin_client.get(
            "/api/internal/ops/notifications/email",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["sent_today"] == 0
    assert data["failed_today"] == 0


def test_email_status_requires_auth(client):
    """Email status endpoint requires admin token."""
    response = client.get("/api/internal/ops/notifications/email")
    assert response.status_code == 401
