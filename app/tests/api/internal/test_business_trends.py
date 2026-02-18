"""
Tests for GET /api/internal/business/trends.

"""
from __future__ import annotations

import pytest
from unittest.mock import patch

from app.core.settings import settings
from app.infrastructure.db.queries.business_trends import DailyCount, TrendSeries

VALID_TOKEN = "test-admin-token-abc123"

# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

_DAILY_7 = [DailyCount(date=f"2025-01-{i:02d}", count=i) for i in range(1, 8)]

_USER_TREND = TrendSeries(
    daily=_DAILY_7,
    total=28,
    average_per_day=4.0,
    peak_date="2025-01-07",
    peak_count=7,
    change_pct=75.0,
)

_VAULT_TREND = TrendSeries(
    daily=_DAILY_7,
    total=14,
    average_per_day=2.0,
    peak_date="2025-01-07",
    peak_count=7,
    change_pct=50.0,
)


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
def mock_trends():
    """
    Patch both query functions at the endpoint module level.

    Patching at the endpoint import target (not the query module)
    ensures the mock is in scope when the endpoint calls the function.
    """
    with patch(
        "app.api.internal.business.trends.get_user_signup_trend",
        return_value=_USER_TREND,
    ), patch(
        "app.api.internal.business.trends.get_vault_provisioning_trend",
        return_value=_VAULT_TREND,
    ):
        yield


# =============================================================================
# TESTS
# =============================================================================

def test_trends_returns_200(admin_client, mock_trends):
    """Trends endpoint returns 200 with valid token."""
    response = admin_client.get(
        "/api/internal/business/trends",
        headers={"X-Admin-Token": VALID_TOKEN},
    )
    assert response.status_code == 200


def test_trends_requires_auth(admin_client, mock_trends):
    """Trends endpoint rejects requests without token."""
    response = admin_client.get("/api/internal/business/trends")
    assert response.status_code == 401


def test_trends_rejects_wrong_token(admin_client, mock_trends):
    """Trends endpoint rejects wrong token."""
    response = admin_client.get(
        "/api/internal/business/trends",
        headers={"X-Admin-Token": "wrong-token"},
    )
    assert response.status_code == 401


def test_trends_returns_user_signups(admin_client, mock_trends):
    """Response contains user_signups series."""
    response = admin_client.get(
        "/api/internal/business/trends",
        headers={"X-Admin-Token": VALID_TOKEN},
    )
    data = response.json()
    assert data["user_signups"]["total"] == 28
    assert data["user_signups"]["average_per_day"] == 4.0
    assert data["user_signups"]["peak_date"] == "2025-01-07"
    assert data["user_signups"]["peak_count"] == 7
    assert data["user_signups"]["change_pct"] == 75.0


def test_trends_returns_vault_provisioning(admin_client, mock_trends):
    """Response contains vault_provisioning series."""
    response = admin_client.get(
        "/api/internal/business/trends",
        headers={"X-Admin-Token": VALID_TOKEN},
    )
    data = response.json()
    assert data["vault_provisioning"]["total"] == 14
    assert data["vault_provisioning"]["peak_count"] == 7
    assert data["vault_provisioning"]["change_pct"] == 50.0


def test_trends_daily_length_matches_days_param(admin_client, mock_trends):
    """daily[] always contains exactly `days` entries."""
    response = admin_client.get(
        "/api/internal/business/trends",
        headers={"X-Admin-Token": VALID_TOKEN},
        params={"days": 7},
    )
    data = response.json()
    assert len(data["user_signups"]["daily"]) == 7
    assert len(data["vault_provisioning"]["daily"]) == 7


def test_trends_passes_days_param_to_queries(admin_client):
    """days query param is forwarded to both query functions."""
    with patch(
        "app.api.internal.business.trends.get_user_signup_trend",
        return_value=_USER_TREND,
    ) as mock_user, patch(
        "app.api.internal.business.trends.get_vault_provisioning_trend",
        return_value=_VAULT_TREND,
    ) as mock_vault:
        admin_client.get(
            "/api/internal/business/trends",
            headers={"X-Admin-Token": VALID_TOKEN},
            params={"days": 14},
        )

    _, user_kwargs = mock_user.call_args
    _, vault_kwargs = mock_vault.call_args
    assert user_kwargs["days"] == 14
    assert vault_kwargs["days"] == 14


def test_trends_contains_period_metadata(admin_client, mock_trends):
    """Response includes period_days, period_start, period_end."""
    response = admin_client.get(
        "/api/internal/business/trends",
        headers={"X-Admin-Token": VALID_TOKEN},
    )
    data = response.json()
    assert "period_days" in data
    assert "period_start" in data
    assert "period_end" in data
    assert "generated_at" in data


def test_trends_days_param_minimum(admin_client, mock_trends):
    """days param below minimum (7) is rejected."""
    response = admin_client.get(
        "/api/internal/business/trends",
        headers={"X-Admin-Token": VALID_TOKEN},
        params={"days": 3},
    )
    assert response.status_code == 422


def test_trends_days_param_maximum(admin_client, mock_trends):
    """days param above maximum (90) is rejected."""
    response = admin_client.get(
        "/api/internal/business/trends",
        headers={"X-Admin-Token": VALID_TOKEN},
        params={"days": 91},
    )
    assert response.status_code == 422