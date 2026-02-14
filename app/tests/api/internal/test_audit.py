"""
Tests for audit log endpoint.

Patch target: app.api.internal.ops.audit.get_audit_logs
(where it's used, not where it's defined)
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.core.settings import settings
from app.infrastructure.db.queries.audit_queries import AuditLogEntry, PaginatedAuditLogs

VALID_TOKEN = "test-admin-token-abc123"

_PATCH_TARGET = "app.api.internal.ops.audit.get_audit_logs"


@pytest.fixture
def admin_client(app, vault_repo, vault_auth_repo, user_repo, rate_limiter):
    from fastapi.testclient import TestClient
    with patch.object(settings, "ADMIN_API_TOKEN", VALID_TOKEN):
        with TestClient(app) as c:
            yield c


def _make_entry(n: int) -> AuditLogEntry:
    return AuditLogEntry(
        id=n,
        action="SESSION_REVOKED",
        target_type="user",
        target_id=f"user-{n}",
        details={"reason": "admin action"},
        ip_address=None,
        created_at=datetime.now(timezone.utc),
    )


def test_audit_logs_returns_paginated_response(admin_client):
    """Audit logs endpoint returns correct pagination structure."""
    def mock_get(db, *, page, limit, action):
        return PaginatedAuditLogs(
            items=[_make_entry(1), _make_entry(2)],
            total=2,
            page=1,
            pages=1,
        )

    with patch(_PATCH_TARGET, mock_get):
        response = admin_client.get(
            "/api/internal/ops/audit",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["page"] == 1
    assert data["pages"] == 1
    assert len(data["items"]) == 2
    assert data["items"][0]["action"] == "SESSION_REVOKED"
    assert data["items"][0]["target_type"] == "user"


def test_audit_logs_empty_initially(admin_client):
    """Audit logs returns empty list when no entries exist."""
    def mock_get(db, *, page, limit, action):
        return PaginatedAuditLogs(items=[], total=0, page=1, pages=0)

    with patch(_PATCH_TARGET, mock_get):
        response = admin_client.get(
            "/api/internal/ops/audit",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_audit_logs_pagination_params(admin_client):
    """Audit logs respects page and limit query params."""
    captured = {}

    def mock_get(db, *, page, limit, action):
        captured["page"] = page
        captured["limit"] = limit
        captured["action"] = action
        return PaginatedAuditLogs(items=[], total=0, page=page, pages=0)

    with patch(_PATCH_TARGET, mock_get):
        admin_client.get(
            "/api/internal/ops/audit?page=2&limit=10&action=API_KEY_CREATED",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    assert captured["page"] == 2
    assert captured["limit"] == 10
    assert captured["action"] == "API_KEY_CREATED"


def test_audit_logs_requires_auth(client):
    """Audit logs requires admin token."""
    response = client.get("/api/internal/ops/audit")
    assert response.status_code == 401
