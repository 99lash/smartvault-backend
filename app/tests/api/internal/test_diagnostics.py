"""
Tests for diagnostics endpoints.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.core.settings import settings
from app.infrastructure.db.queries.system_metrics import (
    RedisHealthMetrics,
    DatabasePoolMetrics,
)

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


# =============================================================================
# REDIS DIAGNOSTICS TESTS
# =============================================================================

def test_redis_diagnostics_returns_healthy(admin_client):
    """Redis diagnostics returns health status when Redis is available."""
    from app.infrastructure.db.queries import system_metrics
    
    # Mock successful Redis query
    async def mock_get_redis_health():
        return RedisHealthMetrics(
            status="healthy",
            connected=True,
            memory_used_mb=45.67,
            total_keys=1234,
            uptime_seconds=86400,
        )
    
    with patch.object(system_metrics, "get_redis_health", mock_get_redis_health):
        response = admin_client.get(
            "/api/internal/ops/diagnostics/redis",
            headers={"X-Admin-Token": VALID_TOKEN},
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["connected"] is True
    assert data["memory_used_mb"] == 45.67
    assert data["total_keys"] == 1234
    assert data["uptime_seconds"] == 86400
    assert "checked_at" in data


def test_redis_diagnostics_returns_unhealthy_on_error(admin_client):
    """Redis diagnostics returns unhealthy when Redis is down."""
    from app.infrastructure.db.queries import system_metrics
    
    # Mock Redis failure
    async def mock_get_redis_health():
        return RedisHealthMetrics(
            status="unhealthy",
            connected=False,
            memory_used_mb=0.0,
            total_keys=0,
            uptime_seconds=0,
        )
    
    with patch.object(system_metrics, "get_redis_health", mock_get_redis_health):
        response = admin_client.get(
            "/api/internal/ops/diagnostics/redis",
            headers={"X-Admin-Token": VALID_TOKEN},
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["connected"] is False


def test_redis_diagnostics_requires_auth(client):
    """Redis diagnostics requires admin token."""
    response = client.get("/api/internal/ops/diagnostics/redis")
    assert response.status_code == 401


# =============================================================================
# WEBSOCKET DIAGNOSTICS TESTS
# =============================================================================

def test_websocket_diagnostics_returns_stats(admin_client):
    """WebSocket diagnostics returns connection statistics."""
    from app.infrastructure.messaging import websocket_manager
    
    # Mock WebSocket manager stats
    mock_manager = MagicMock()
    mock_manager.get_connection_stats.return_value = {
        "total_users": 5,
        "total_user_connections": 7,
        "total_vaults": 3,
        "subscriptions": 8,
    }
    mock_manager.get_online_vaults.return_value = [
        "vault-1",
        "vault-2",
        "vault-3",
    ]
    
    with patch.object(websocket_manager, "manager", mock_manager):
        response = admin_client.get(
            "/api/internal/ops/diagnostics/websockets",
            headers={"X-Admin-Token": VALID_TOKEN},
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_users"] == 5
    assert data["total_user_connections"] == 7
    assert data["total_vaults"] == 3
    assert data["subscriptions"] == 8
    assert data["online_vaults"] == ["vault-1", "vault-2", "vault-3"]
    assert "checked_at" in data


def test_websocket_diagnostics_handles_no_connections(admin_client):
    """WebSocket diagnostics handles zero connections gracefully."""
    from app.infrastructure.messaging import websocket_manager
    
    # Mock empty stats
    mock_manager = MagicMock()
    mock_manager.get_connection_stats.return_value = {
        "total_users": 0,
        "total_user_connections": 0,
        "total_vaults": 0,
        "subscriptions": 0,
    }
    mock_manager.get_online_vaults.return_value = []
    
    with patch.object(websocket_manager, "manager", mock_manager):
        response = admin_client.get(
            "/api/internal/ops/diagnostics/websockets",
            headers={"X-Admin-Token": VALID_TOKEN},
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_users"] == 0
    assert data["online_vaults"] == []


def test_websocket_diagnostics_requires_auth(client):
    """WebSocket diagnostics requires admin token."""
    response = client.get("/api/internal/ops/diagnostics/websockets")
    assert response.status_code == 401


# =============================================================================
# DATABASE DIAGNOSTICS TESTS
# =============================================================================

def test_database_diagnostics_returns_pool_stats(admin_client):
    """Database diagnostics returns pool statistics."""
    from app.infrastructure.db.queries import system_metrics
    
    # Mock database pool metrics
    def mock_get_db_pool_metrics(db):
        return DatabasePoolMetrics(
            status="healthy",
            pool_size=10,
            checked_out=3,
            overflow=0,
        )
    
    with patch.object(system_metrics, "get_database_pool_metrics", mock_get_db_pool_metrics):
        response = admin_client.get(
            "/api/internal/ops/diagnostics/database",
            headers={"X-Admin-Token": VALID_TOKEN},
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["pool_size"] == 10
    assert data["checked_out"] == 3
    assert data["overflow"] == 0
    assert "checked_at" in data


def test_database_diagnostics_handles_errors(admin_client):
    """Database diagnostics handles pool errors gracefully."""
    from app.infrastructure.db.queries import system_metrics
    
    # Mock error condition
    def mock_get_db_pool_metrics(db):
        return DatabasePoolMetrics(
            status="unknown",
            pool_size=0,
            checked_out=0,
            overflow=0,
        )
    
    with patch.object(system_metrics, "get_database_pool_metrics", mock_get_db_pool_metrics):
        response = admin_client.get(
            "/api/internal/ops/diagnostics/database",
            headers={"X-Admin-Token": VALID_TOKEN},
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unknown"


def test_database_diagnostics_requires_auth(client):
    """Database diagnostics requires admin token."""
    response = client.get("/api/internal/ops/diagnostics/database")
    assert response.status_code == 401


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

def test_all_diagnostics_endpoints_registered(admin_client):
    """All three diagnostics endpoints are properly registered."""
    endpoints = [
        "/api/internal/ops/diagnostics/redis",
        "/api/internal/ops/diagnostics/websockets",
        "/api/internal/ops/diagnostics/database",
    ]
    
    for endpoint in endpoints:
        response = admin_client.get(
            endpoint,
            headers={"X-Admin-Token": VALID_TOKEN},
        )
        # Should return 200 (not 404)
        assert response.status_code == 200, f"Endpoint {endpoint} not registered"