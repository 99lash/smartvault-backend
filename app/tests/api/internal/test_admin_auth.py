from __future__ import annotations

import pytest
from unittest.mock import patch

from app.core.settings import settings

VALID_TOKEN = "test-admin-token-abc123"


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def admin_client(app, vault_repo, vault_auth_repo, user_repo, rate_limiter):
    """Test client with valid admin token configured."""
    from fastapi.testclient import TestClient

    with patch.object(settings, "ADMIN_API_TOKEN", VALID_TOKEN):
        with TestClient(app) as c:
            yield c


@pytest.fixture
def unconfigured_client(app, vault_repo, vault_auth_repo, user_repo, rate_limiter):
    """Test client with no admin token configured."""
    from fastapi.testclient import TestClient

    with patch.object(settings, "ADMIN_API_TOKEN", None):
        with TestClient(app) as c:
            yield c


# =============================================================================
# AUTHENTICATION TESTS
# =============================================================================

def test_ping_without_token_returns_401(app, vault_repo, vault_auth_repo, user_repo, rate_limiter):
    """Request without X-Admin-Token header returns 401."""
    from fastapi.testclient import TestClient

    with patch.object(settings, "ADMIN_API_TOKEN", VALID_TOKEN):
        with TestClient(app) as client:
            response = client.get("/api/internal/ping")

    assert response.status_code == 401


def test_ping_with_wrong_token_returns_401(app, vault_repo, vault_auth_repo, user_repo, rate_limiter):
    """Request with wrong token returns 401."""
    from fastapi.testclient import TestClient

    with patch.object(settings, "ADMIN_API_TOKEN", VALID_TOKEN):
        with TestClient(app) as client:
            response = client.get(
                "/api/internal/ping",
                headers={"X-Admin-Token": "wrong-token"},
            )

    assert response.status_code == 401


def test_ping_with_correct_token_returns_200(admin_client):
    """Request with correct token returns 200."""
    response = admin_client.get(
        "/api/internal/ping",
        headers={"X-Admin-Token": VALID_TOKEN},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["admin_api"] == "operational"


def test_ping_not_configured_returns_503(unconfigured_client):
    """When ADMIN_API_TOKEN not set, returns 503."""
    response = unconfigured_client.get(
        "/api/internal/ping",
        headers={"X-Admin-Token": "any-token"},
    )

    assert response.status_code == 503


def test_internal_endpoints_hidden_from_public_docs(admin_client):
    """Internal endpoints do not appear in public OpenAPI schema."""
    response = admin_client.get("/openapi.json")
    paths = response.json().get("paths", {})
    internal_paths = [p for p in paths if p.startswith("/api/internal")]

    assert len(internal_paths) == 0


def test_public_health_endpoint_unaffected(admin_client):
    """Public endpoints work without admin token."""
    response = admin_client.get("/api/v1/health")

    assert response.status_code == 200