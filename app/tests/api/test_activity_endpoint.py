from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.deps.activity import get_activity_log_repo
from app.infrastructure.db.repositories.in_memory_activity_log_repository import (
    InMemoryActivityLogRepository,
)
from app.domain.models.access_log import AccessLog


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def activity_repo(app):
    """Override activity log repo with in-memory fake."""
    repo = InMemoryActivityLogRepository()
    app.dependency_overrides[get_activity_log_repo] = lambda: repo
    yield repo
    app.dependency_overrides.pop(get_activity_log_repo, None)
    repo.clear()


@pytest.fixture
def client(app, vault_repo, vault_auth_repo, user_repo, rate_limiter, activity_repo):
    with TestClient(app) as c:
        yield c


def _make_log(vault_id: str, action: str = "VAULT_UNLOCKED") -> AccessLog:
    return AccessLog(
        id=f"log-{uuid4()}",
        vault_id=vault_id,
        user_id="demo-user-1",
        action=action,          # type: ignore[arg-type]
        method="PIN",           # type: ignore[arg-type]
        metadata=None,
        created_at=datetime.now(timezone.utc),
    )

def _set_vault_owner(vault_repo, vault_id: str, owner_id: str) -> None:
    """
    Transfer vault ownership to the given user.

    Mirrors the same pattern used in test_pin_endpoints.py.
    Required because InMemoryVaultRepository seeds vaults owned
    by 'demo-user-1', but auth bypass returns 'test-user-id'.
    """
    vault = vault_repo._vaults[vault_id]
    vault_repo._vaults[vault_id] = replace(vault, owner_id=owner_id)
    
# =============================================================================
# GET /api/v1/vaults/{vault_id}/activity
# =============================================================================

def test_activity_returns_200_for_authorised_user(client, vault_repo, activity_repo):
    """Owner can fetch activity for their vault."""
    _set_vault_owner(vault_repo, "demo-vault-1", "test-user-id")
    activity_repo.create(_make_log("demo-vault-1"))

    response = client.get("/api/v1/vaults/demo-vault-1/activity")

    assert response.status_code == 200


def test_activity_returns_entries(client, vault_repo, activity_repo):
    """Response contains the stored log entries."""
    _set_vault_owner(vault_repo, "demo-vault-1", "test-user-id")
    activity_repo.create(_make_log("demo-vault-1", action="PIN_SET"))
    activity_repo.create(_make_log("demo-vault-1", action="VAULT_UNLOCKED"))

    response = client.get("/api/v1/vaults/demo-vault-1/activity")
    data = response.json()

    assert data["vault_id"] == "demo-vault-1"
    assert data["count"] == 2
    assert len(data["entries"]) == 2


def test_activity_entry_fields(client, vault_repo, activity_repo):
    """Each entry contains all expected fields."""
    _set_vault_owner(vault_repo, "demo-vault-1", "test-user-id")
    activity_repo.create(_make_log("demo-vault-1"))

    response = client.get("/api/v1/vaults/demo-vault-1/activity")
    entry = response.json()["entries"][0]

    assert "id" in entry
    assert "vault_id" in entry
    assert "action" in entry
    assert "method" in entry
    assert "created_at" in entry
    assert "user_id" in entry
    assert "metadata" in entry


def test_activity_returns_403_for_unknown_vault(client, vault_repo, activity_repo):
    """Non-existent vault returns 403 (no access = no access)."""
    response = client.get("/api/v1/vaults/does-not-exist/activity")

    assert response.status_code == 403


def test_activity_respects_limit_param(client, vault_repo, activity_repo):
    """limit query param restricts number of entries returned."""
    _set_vault_owner(vault_repo, "demo-vault-1", "test-user-id")
    for _ in range(10):
        activity_repo.create(_make_log("demo-vault-1"))

    response = client.get("/api/v1/vaults/demo-vault-1/activity?limit=3")
    data = response.json()

    assert data["count"] == 3
    assert len(data["entries"]) == 3


def test_activity_empty_vault_returns_empty_list(client, vault_repo, activity_repo):
    """Vault with no logs returns empty entries list."""
    _set_vault_owner(vault_repo, "demo-vault-1", "test-user-id")
    response = client.get("/api/v1/vaults/demo-vault-1/activity")
    data = response.json()

    assert data["count"] == 0
    assert data["entries"] == []


def test_activity_filters_by_vault(client, vault_repo, activity_repo):
    """Only entries for the requested vault are returned."""
    _set_vault_owner(vault_repo, "demo-vault-1", "test-user-id")
    activity_repo.create(_make_log("demo-vault-1"))
    activity_repo.create(_make_log("demo-vault-2"))

    response = client.get("/api/v1/vaults/demo-vault-1/activity")
    data = response.json()

    assert data["count"] == 1
    assert data["entries"][0]["vault_id"] == "demo-vault-1"