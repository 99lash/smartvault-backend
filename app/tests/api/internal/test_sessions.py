"""
Tests for session stats and session revoke endpoints.

Patch targets are in app.api.internal.ops.sessions (where the names
are used), not in app.infrastructure.services.session_metrics.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.settings import settings
from app.infrastructure.services.session_metrics import SessionMetrics

VALID_TOKEN = "test-admin-token-abc123"

_PATCH_STATS  = "app.api.internal.ops.sessions.get_session_metrics"
_PATCH_REVOKE = "app.api.internal.ops.sessions.revoke_user_sessions"


@pytest.fixture
def admin_client(app, vault_repo, vault_auth_repo, user_repo, rate_limiter):
    from fastapi.testclient import TestClient
    with patch.object(settings, "ADMIN_API_TOKEN", VALID_TOKEN):
        with TestClient(app) as c:
            yield c


# =============================================================================
# SESSION STATS TESTS
# =============================================================================

def test_session_stats_returns_metrics(admin_client):
    """Session stats returns total tokens and top users."""
    def mock_get():
        return SessionMetrics(
            total_active_tokens=15,
            top_users=[
                {"user_id": "user-aaa", "token_count": 3},
                {"user_id": "user-bbb", "token_count": 2},
            ],
        )

    with patch(_PATCH_STATS, mock_get):
        response = admin_client.get(
            "/api/internal/ops/sessions/stats",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total_active_tokens"] == 15
    assert len(data["top_users"]) == 2
    assert data["top_users"][0]["user_id"] == "user-aaa"
    assert data["top_users"][0]["token_count"] == 3
    assert "checked_at" in data


def test_session_stats_empty_when_no_tokens(admin_client):
    """Session stats handles zero tokens gracefully."""
    def mock_get():
        return SessionMetrics(total_active_tokens=0, top_users=[])

    with patch(_PATCH_STATS, mock_get):
        response = admin_client.get(
            "/api/internal/ops/sessions/stats",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total_active_tokens"] == 0
    assert data["top_users"] == []


def test_session_stats_requires_auth(client):
    """Session stats requires admin token."""
    response = client.get("/api/internal/ops/sessions/stats")
    assert response.status_code == 401


# =============================================================================
# SESSION REVOKE TESTS
# =============================================================================

def test_revoke_user_sessions_returns_count(admin_client):
    """Revoke endpoint returns number of sessions revoked."""
    def mock_revoke(user_id: str) -> int:
        return 3

    with patch(_PATCH_REVOKE, mock_revoke):
        response = admin_client.delete(
            "/api/internal/ops/sessions/user-test-123",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user-test-123"
    assert data["sessions_revoked"] == 3


def test_revoke_returns_zero_for_unknown_user(admin_client):
    """Revoke returns 0 for a user with no sessions (not 404)."""
    def mock_revoke(user_id: str) -> int:
        return 0

    with patch(_PATCH_REVOKE, mock_revoke):
        response = admin_client.delete(
            "/api/internal/ops/sessions/no-such-user",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    assert response.status_code == 200
    assert response.json()["sessions_revoked"] == 0


def test_revoke_requires_auth(client):
    """Revoke endpoint requires admin token."""
    response = client.delete("/api/internal/ops/sessions/user-123")
    assert response.status_code == 401
