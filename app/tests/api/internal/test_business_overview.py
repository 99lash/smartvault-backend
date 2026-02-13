from __future__ import annotations

import pytest
from unittest.mock import patch

from app.core.settings import settings
from app.infrastructure.db.queries.business_metrics import (
    MemberMetrics,
    UserMetrics,
    VaultMetrics,
)

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


@pytest.fixture
def mock_metrics():
    """
    Patch all DB query functions with predictable test data.

    Avoids requiring a real database in tests.
    """
    with patch(
        "app.api.internal.business.overview.get_user_metrics",
        return_value=UserMetrics(total=100, new_today=5, new_this_week=20),
    ), patch(
        "app.api.internal.business.overview.get_vault_metrics",
        return_value=VaultMetrics(
            total=80,
            with_pin=60,
            by_status={"ONLINE": 30, "OFFLINE": 50},
        ),
    ), patch(
        "app.api.internal.business.overview.get_member_metrics",
        return_value=MemberMetrics(
            total_authorizations=150,
            by_role={"MEMBER": 120, "VIEWER": 30},
        ),
    ):
        yield


# =============================================================================
# OVERVIEW ENDPOINT TESTS
# =============================================================================

def test_overview_returns_200(admin_client, mock_metrics):
    """Business overview returns 200 with valid token."""
    response = admin_client.get(
        "/api/internal/business/overview",
        headers={"X-Admin-Token": VALID_TOKEN},
    )

    assert response.status_code == 200


def test_overview_returns_user_metrics(admin_client, mock_metrics):
    """Response contains correct user metrics."""
    response = admin_client.get(
        "/api/internal/business/overview",
        headers={"X-Admin-Token": VALID_TOKEN},
    )
    data = response.json()

    assert data["users"]["total"] == 100
    assert data["users"]["new_today"] == 5
    assert data["users"]["new_this_week"] == 20


def test_overview_returns_vault_metrics(admin_client, mock_metrics):
    """Response contains correct vault metrics."""
    response = admin_client.get(
        "/api/internal/business/overview",
        headers={"X-Admin-Token": VALID_TOKEN},
    )
    data = response.json()

    assert data["vaults"]["total"] == 80
    assert data["vaults"]["with_pin"] == 60
    assert data["vaults"]["by_status"]["ONLINE"] == 30
    assert data["vaults"]["by_status"]["OFFLINE"] == 50


def test_overview_returns_member_metrics(admin_client, mock_metrics):
    """Response contains correct member metrics."""
    response = admin_client.get(
        "/api/internal/business/overview",
        headers={"X-Admin-Token": VALID_TOKEN},
    )
    data = response.json()

    assert data["members"]["total_authorizations"] == 150
    assert data["members"]["by_role"]["MEMBER"] == 120
    assert data["members"]["by_role"]["VIEWER"] == 30


def test_overview_contains_generated_at(admin_client, mock_metrics):
    """Response includes generated_at timestamp."""
    response = admin_client.get(
        "/api/internal/business/overview",
        headers={"X-Admin-Token": VALID_TOKEN},
    )
    data = response.json()

    assert "generated_at" in data
    assert data["generated_at"] is not None


def test_overview_requires_admin_token(admin_client, mock_metrics):
    """Business overview rejects requests without token."""
    response = admin_client.get("/api/internal/business/overview")

    assert response.status_code == 401


def test_overview_rejects_wrong_token(admin_client, mock_metrics):
    """Business overview rejects wrong token."""
    response = admin_client.get(
        "/api/internal/business/overview",
        headers={"X-Admin-Token": "wrong-token"},
    )

    assert response.status_code == 401