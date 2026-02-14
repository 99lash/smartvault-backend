"""
Tests for ops dashboard summary endpoint and activity endpoint.

Uses mocked query functions for fast, isolated tests.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch

from app.core.settings import settings
from app.infrastructure.db.queries.activity_queries import ActivitySummary
from app.infrastructure.db.queries.business_metrics import (
    MemberMetrics,
    UserMetrics,
    VaultMetrics,
)
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


def _mock_all_queries(
    users: UserMetrics | None = None,
    vaults: VaultMetrics | None = None,
    members: MemberMetrics | None = None,
    security: SecuritySummary | None = None,
    activity: ActivitySummary | None = None,
):
    """Patch all query functions used by ops summary."""
    return (
        patch(
            "app.api.internal.ops.summary.get_user_metrics",
            return_value=users or UserMetrics(total=50, new_today=2, new_this_week=8),
        ),
        patch(
            "app.api.internal.ops.summary.get_vault_metrics",
            return_value=vaults or VaultMetrics(
                total=40, with_pin=30, by_status={"ONLINE": 20, "OFFLINE": 20}
            ),
        ),
        patch(
            "app.api.internal.ops.summary.get_member_metrics",
            return_value=members or MemberMetrics(
                total_authorizations=60, by_role={"MEMBER": 50, "VIEWER": 10}
            ),
        ),
        patch(
            "app.api.internal.ops.summary.get_security_summary",
            return_value=security or SecuritySummary(
                failed_unlocks_1h=0,
                failed_unlocks_24h=0,
                pin_lockouts_24h=0,
            ),
        ),
        patch(
            "app.api.internal.ops.summary.get_activity_summary",
            return_value=activity or ActivitySummary(
                total_events=25,
                vault_unlocks=15,
                failed_unlocks=2,
                pin_operations=3,
                member_changes=2,
                state_changes=3,
            ),
        ),
    )


# =============================================================================
# OPS SUMMARY TESTS
# =============================================================================

def test_ops_summary_returns_200(admin_client):
    """Ops summary returns 200 with valid token."""
    with _mock_all_queries()[0], _mock_all_queries()[1], \
         _mock_all_queries()[2], _mock_all_queries()[3], \
         _mock_all_queries()[4]:
        response = admin_client.get(
            "/api/internal/ops/summary",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    assert response.status_code == 200


def test_ops_summary_ok_when_no_alerts(admin_client):
    """Overall status is ok when no security thresholds breached."""
    patches = _mock_all_queries()
    with patches[0], patches[1], patches[2], patches[3], patches[4]:
        response = admin_client.get(
            "/api/internal/ops/summary",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    data = response.json()
    assert data["overall_status"] == "ok"
    assert data["security"]["status"] == "ok"
    assert data["security"]["alert_count"] == 0


def test_ops_summary_warning_on_security_alert(admin_client):
    """Overall status reflects security warning."""
    patches = _mock_all_queries(
        security=SecuritySummary(
            failed_unlocks_1h=8,
            failed_unlocks_24h=15,
            pin_lockouts_24h=0,
        )
    )
    with patches[0], patches[1], patches[2], patches[3], patches[4]:
        response = admin_client.get(
            "/api/internal/ops/summary",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    data = response.json()
    assert data["overall_status"] == "warning"
    assert data["security"]["status"] == "warning"
    assert data["security"]["alert_count"] == 1


def test_ops_summary_critical_on_severe_alert(admin_client):
    """Overall status is critical when critical threshold breached."""
    patches = _mock_all_queries(
        security=SecuritySummary(
            failed_unlocks_1h=25,
            failed_unlocks_24h=50,
            pin_lockouts_24h=0,
        )
    )
    with patches[0], patches[1], patches[2], patches[3], patches[4]:
        response = admin_client.get(
            "/api/internal/ops/summary",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    data = response.json()
    assert data["overall_status"] == "critical"


def test_ops_summary_contains_business_metrics(admin_client):
    """Response includes correct business metrics."""
    patches = _mock_all_queries(
        users=UserMetrics(total=100, new_today=5, new_this_week=20),
        vaults=VaultMetrics(total=80, with_pin=60, by_status={"ONLINE": 30}),
    )
    with patches[0], patches[1], patches[2], patches[3], patches[4]:
        response = admin_client.get(
            "/api/internal/ops/summary",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    data = response.json()
    assert data["business"]["users"]["total"] == 100
    assert data["business"]["users"]["new_today"] == 5
    assert data["business"]["vaults"]["total"] == 80
    assert data["business"]["vaults"]["with_pin"] == 60


def test_ops_summary_contains_activity_metrics(admin_client):
    """Response includes correct activity summary."""
    patches = _mock_all_queries(
        activity=ActivitySummary(
            total_events=30,
            vault_unlocks=20,
            failed_unlocks=5,
            pin_operations=2,
            member_changes=1,
            state_changes=2,
        )
    )
    with patches[0], patches[1], patches[2], patches[3], patches[4]:
        response = admin_client.get(
            "/api/internal/ops/summary",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    data = response.json()
    assert data["activity"]["total_events"] == 30
    assert data["activity"]["vault_unlocks"] == 20
    assert data["activity"]["failed_unlocks"] == 5
    assert data["activity"]["period_hours"] == 24


def test_ops_summary_requires_admin_token(admin_client):
    """Ops summary rejects requests without token."""
    response = admin_client.get("/api/internal/ops/summary")

    assert response.status_code == 401


def test_ops_summary_contains_generated_at(admin_client):
    """Response includes generated_at timestamp."""
    patches = _mock_all_queries()
    with patches[0], patches[1], patches[2], patches[3], patches[4]:
        response = admin_client.get(
            "/api/internal/ops/summary",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    assert "generated_at" in response.json()


# =============================================================================
# ACTIVITY ENDPOINT TESTS
# =============================================================================

def test_activity_endpoint_returns_200(admin_client):
    """Activity endpoint returns 200 with valid token."""
    with patch(
        "app.api.internal.business.activity.get_recent_activity",
        return_value=[],
    ), patch(
        "app.api.internal.business.activity.get_activity_summary",
        return_value=ActivitySummary(
            total_events=0,
            vault_unlocks=0,
            failed_unlocks=0,
            pin_operations=0,
            member_changes=0,
            state_changes=0,
        ),
    ):
        response = admin_client.get(
            "/api/internal/business/activity",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    assert response.status_code == 200


def test_activity_endpoint_respects_hours_param(admin_client):
    """Activity endpoint reflects the requested hours window."""
    with patch(
        "app.api.internal.business.activity.get_recent_activity",
        return_value=[],
    ), patch(
        "app.api.internal.business.activity.get_activity_summary",
        return_value=ActivitySummary(
            total_events=0, vault_unlocks=0, failed_unlocks=0,
            pin_operations=0, member_changes=0, state_changes=0,
        ),
    ):
        response = admin_client.get(
            "/api/internal/business/activity?hours=48",
            headers={"X-Admin-Token": VALID_TOKEN},
        )

    data = response.json()
    assert data["period_hours"] == 48


def test_activity_endpoint_requires_admin_token(admin_client):
    """Activity endpoint rejects requests without token."""
    response = admin_client.get("/api/internal/business/activity")

    assert response.status_code == 401