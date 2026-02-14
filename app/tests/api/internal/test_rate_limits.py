"""
Tests for rate limits dashboard endpoint.

Patch target: app.api.internal.ops.rate_limits.get_rate_limit_metrics
(where it's used, not where it's defined — because the endpoint does
`from module import function`, creating a local reference)
"""
from __future__ import annotations

from unittest.mock import patch, AsyncMock

import pytest

from app.core.settings import settings
from app.infrastructure.db.queries.rate_limit_metrics import (
    RateLimitMetrics,
    RateLimitViolator,
)

VALID_TOKEN = "test-admin-token-abc123"

_PATCH_TARGET = "app.api.internal.ops.rate_limits.get_rate_limit_metrics"


@pytest.fixture
def admin_client(app, vault_repo, vault_auth_repo, user_repo, rate_limiter):
    from fastapi.testclient import TestClient
    with patch.object(settings, "ADMIN_API_TOKEN", VALID_TOKEN):
        with TestClient(app) as c:
            yield c


# =============================================================================
# TESTS
# =============================================================================

def test_rate_limits_returns_200(admin_client):
    """Rate limits endpoint returns 200 with mocked metrics."""
    mock = AsyncMock(return_value=RateLimitMetrics(
        total_active_keys=3,
        top_violators=[
            RateLimitViolator(key="pin:user-1", current_count=8, ttl_seconds=55),
            RateLimitViolator(key="auth:user-2", current_count=5, ttl_seconds=30),
        ],
        by_category={"pin": 2, "auth": 1},
    ))

    with patch(_PATCH_TARGET, mock):
        response = admin_client.get(
            "/api/internal/ops/rate-limits",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total_active_keys"] == 3
    assert len(data["top_violators"]) == 2
    assert data["top_violators"][0]["key"] == "pin:user-1"
    assert data["top_violators"][0]["current_count"] == 8
    assert data["by_category"] == {"pin": 2, "auth": 1}
    assert "checked_at" in data


def test_rate_limits_empty_when_no_violations(admin_client):
    """Rate limits returns empty violators when Redis is clean."""
    mock = AsyncMock(return_value=RateLimitMetrics(
        total_active_keys=0,
        top_violators=[],
        by_category={},
    ))

    with patch(_PATCH_TARGET, mock):
        response = admin_client.get(
            "/api/internal/ops/rate-limits",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total_active_keys"] == 0
    assert data["top_violators"] == []
    assert data["by_category"] == {}


def test_rate_limits_requires_auth(client):
    """Rate limits endpoint requires admin token."""
    response = client.get("/api/internal/ops/rate-limits")
    assert response.status_code == 401
