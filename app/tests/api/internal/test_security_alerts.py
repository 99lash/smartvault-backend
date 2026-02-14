"""
Tests for security alerts endpoint.

Verifies alert generation, severity levels, and
status determination based on mocked security data.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch

from app.core.settings import settings
from app.infrastructure.db.queries.security_metrics import SecuritySummary

VALID_TOKEN = "test-admin-token-abc123"


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def admin_client(app, vault_repo, vault_auth_repo, user_repo, rate_limiter):
    """Test client with valid admin token."""
    from fastapi.testclient import TestClient

    with patch.object(settings, "ADMIN_API_TOKEN", VALID_TOKEN):
        with TestClient(app) as c:
            yield c


def _mock_summary(
    failed_unlocks_1h: int = 0,
    failed_unlocks_24h: int = 0,
    pin_lockouts_24h: int = 0,
):
    """Helper to patch get_security_summary with controlled data."""
    return patch(
        "app.api.internal.security.alerts.get_security_summary",
        return_value=SecuritySummary(
            failed_unlocks_1h=failed_unlocks_1h,
            failed_unlocks_24h=failed_unlocks_24h,
            pin_lockouts_24h=pin_lockouts_24h,
        ),
    )


# =============================================================================
# AUTHENTICATION TESTS
# =============================================================================

def test_alerts_requires_admin_token(admin_client):
    """Security alerts endpoint rejects requests without token."""
    response = admin_client.get("/api/internal/security/alerts")

    assert response.status_code == 401


def test_alerts_rejects_wrong_token(admin_client):
    """Security alerts endpoint rejects wrong token."""
    response = admin_client.get(
        "/api/internal/security/alerts",
        headers={"X-Admin-Token": "wrong-token"},
    )

    assert response.status_code == 401


# =============================================================================
# STATUS TESTS
# =============================================================================

def test_alerts_returns_ok_when_no_suspicious_activity(admin_client):
    """Returns status=ok when all counts are below thresholds."""
    with _mock_summary(failed_unlocks_1h=0, pin_lockouts_24h=0):
        response = admin_client.get(
            "/api/internal/security/alerts",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["active_alerts"] == []


def test_alerts_returns_warning_on_failed_unlock_spike(admin_client):
    """Returns status=warning when failed unlocks exceed warning threshold."""
    with _mock_summary(failed_unlocks_1h=8):
        response = admin_client.get(
            "/api/internal/security/alerts",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    data = response.json()
    assert data["status"] == "warning"
    assert len(data["active_alerts"]) == 1
    assert data["active_alerts"][0]["type"] == "failed_unlock_spike"
    assert data["active_alerts"][0]["severity"] == "high"


def test_alerts_returns_critical_on_severe_unlock_spike(admin_client):
    """Returns status=critical when failed unlocks exceed critical threshold."""
    with _mock_summary(failed_unlocks_1h=25):
        response = admin_client.get(
            "/api/internal/security/alerts",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    data = response.json()
    assert data["status"] == "critical"
    assert data["active_alerts"][0]["severity"] == "critical"


def test_alerts_returns_warning_on_pin_lockout_spike(admin_client):
    """Returns status=warning when PIN lockouts exceed warning threshold."""
    with _mock_summary(pin_lockouts_24h=5):
        response = admin_client.get(
            "/api/internal/security/alerts",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    data = response.json()
    assert data["status"] == "warning"
    assert data["active_alerts"][0]["type"] == "pin_lockout_spike"
    assert data["active_alerts"][0]["severity"] == "medium"


def test_alerts_returns_critical_on_severe_lockout_spike(admin_client):
    """Returns status=critical when PIN lockouts exceed critical threshold."""
    with _mock_summary(pin_lockouts_24h=12):
        response = admin_client.get(
            "/api/internal/security/alerts",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    data = response.json()
    assert data["status"] == "critical"
    assert data["active_alerts"][0]["severity"] == "critical"


def test_alerts_multiple_active_alerts(admin_client):
    """Multiple thresholds breached results in multiple alerts."""
    with _mock_summary(failed_unlocks_1h=8, pin_lockouts_24h=5):
        response = admin_client.get(
            "/api/internal/security/alerts",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    data = response.json()
    assert len(data["active_alerts"]) == 2


# =============================================================================
# RESPONSE STRUCTURE TESTS
# =============================================================================

def test_alerts_contains_generated_at(admin_client):
    """Response includes generated_at timestamp."""
    with _mock_summary():
        response = admin_client.get(
            "/api/internal/security/alerts",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    data = response.json()
    assert "generated_at" in data
    assert data["generated_at"] is not None


def test_alerts_contains_24h_summary(admin_client):
    """Response includes last_24h summary with all fields."""
    with _mock_summary(failed_unlocks_1h=3, failed_unlocks_24h=10, pin_lockouts_24h=1):
        response = admin_client.get(
            "/api/internal/security/alerts",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    data = response.json()
    assert data["last_24h"]["failed_unlocks_1h"] == 3
    assert data["last_24h"]["failed_unlocks_24h"] == 10
    assert data["last_24h"]["pin_lockouts_24h"] == 1


def test_alert_contains_required_fields(admin_client):
    """Each active alert contains all required fields."""
    with _mock_summary(failed_unlocks_1h=8):
        response = admin_client.get(
            "/api/internal/security/alerts",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    alert = response.json()["active_alerts"][0]
    assert "type" in alert
    assert "severity" in alert
    assert "message" in alert
    assert "count" in alert
    assert "threshold" in alert
    assert "window" in alert


def test_alert_count_matches_actual_count(admin_client):
    """Alert count field reflects the actual event count."""
    with _mock_summary(failed_unlocks_1h=12):
        response = admin_client.get(
            "/api/internal/security/alerts",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    alert = response.json()["active_alerts"][0]
    assert alert["count"] == 12


def test_alerts_hidden_from_public_docs(admin_client):
    """Security alerts endpoint is hidden from public OpenAPI schema."""
    response = admin_client.get("/openapi.json")
    paths = response.json().get("paths", {})
    internal_paths = [p for p in paths if p.startswith("/api/internal")]

    assert len(internal_paths) == 0