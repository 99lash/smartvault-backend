"""
Tests for API key management endpoints.

Patch targets are in app.api.internal.ops.api_keys (where the names
are used), not in app.infrastructure.db.queries.api_key_queries.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.core.settings import settings
from app.infrastructure.db.queries.api_key_queries import APIKeyEntry, CreatedAPIKey

VALID_TOKEN = "test-admin-token-abc123"

_PATCH_LIST   = "app.api.internal.ops.api_keys.list_api_keys"
_PATCH_CREATE = "app.api.internal.ops.api_keys.create_api_key"
_PATCH_REVOKE = "app.api.internal.ops.api_keys.revoke_api_key"


@pytest.fixture
def admin_client(app, vault_repo, vault_auth_repo, user_repo, rate_limiter):
    from fastapi.testclient import TestClient
    with patch.object(settings, "ADMIN_API_TOKEN", VALID_TOKEN):
        with TestClient(app) as c:
            yield c


def _make_key_entry(n: int = 1) -> APIKeyEntry:
    return APIKeyEntry(
        id=n,
        name=f"Test Key {n}",
        created_by="admin_console",
        last_used_at=None,
        expires_at=None,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )


# =============================================================================
# LIST TESTS
# =============================================================================

def test_list_api_keys_returns_items(admin_client):
    """List endpoint returns API key items."""
    def mock_list(db, *, active_only):
        return [_make_key_entry(1), _make_key_entry(2)]

    with patch(_PATCH_LIST, mock_list):
        response = admin_client.get(
            "/api/internal/ops/api-keys",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["items"][0]["name"] == "Test Key 1"
    assert data["items"][0]["is_active"] is True


def test_list_api_keys_empty(admin_client):
    """List endpoint handles empty key list."""
    with patch(_PATCH_LIST, lambda db, *, active_only: []):
        response = admin_client.get(
            "/api/internal/ops/api-keys",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    assert response.status_code == 200
    assert response.json()["items"] == []


def test_list_api_keys_requires_auth(client):
    response = client.get("/api/internal/ops/api-keys")
    assert response.status_code == 401


# =============================================================================
# CREATE TESTS
# =============================================================================

def test_create_api_key_returns_plain_key(admin_client):
    """Create endpoint returns a key starting with sk_."""
    def mock_create(db, *, name, created_by, expires_in_days):
        return CreatedAPIKey(
            id=1,
            key="sk_abcdefghijklmnopqrstuvwxyz123456",
            name=name,
            expires_at=None,
        )

    with patch(_PATCH_CREATE, mock_create):
        response = admin_client.post(
            "/api/internal/ops/api-keys",
            headers={"X-Admin-Token": VALID_TOKEN},
            json={"name": "My Integration Key"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["key"].startswith("sk_")
    assert data["name"] == "My Integration Key"
    assert "id" in data


def test_create_api_key_with_expiry(admin_client):
    """Create endpoint passes expires_in_days to query function."""
    captured = {}

    def mock_create(db, *, name, created_by, expires_in_days):
        captured["expires_in_days"] = expires_in_days
        return CreatedAPIKey(id=1, key="sk_xxx", name=name, expires_at=None)

    with patch(_PATCH_CREATE, mock_create):
        admin_client.post(
            "/api/internal/ops/api-keys",
            headers={"X-Admin-Token": VALID_TOKEN},
            json={"name": "Expiring Key", "expires_in_days": 30},
        )

    assert captured["expires_in_days"] == 30


def test_create_api_key_requires_auth(client):
    response = client.post("/api/internal/ops/api-keys", json={"name": "x"})
    assert response.status_code == 401


# =============================================================================
# REVOKE TESTS
# =============================================================================

def test_revoke_api_key_returns_204(admin_client):
    """Revoke endpoint returns 204 No Content on success."""
    with patch(_PATCH_REVOKE, lambda db, *, key_id: True):
        response = admin_client.delete(
            "/api/internal/ops/api-keys/1",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    assert response.status_code == 204


def test_revoke_api_key_returns_404_when_not_found(admin_client):
    """Revoke endpoint returns 404 when key_id doesn't exist."""
    with patch(_PATCH_REVOKE, lambda db, *, key_id: False):
        response = admin_client.delete(
            "/api/internal/ops/api-keys/999",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    assert response.status_code == 404


def test_revoke_api_key_requires_auth(client):
    response = client.delete("/api/internal/ops/api-keys/1")
    assert response.status_code == 401
