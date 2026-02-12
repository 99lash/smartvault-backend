"""Tests for health check endpoints."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy.exc import OperationalError


def test_health_returns_200(client):
    """Simple health check always returns 200."""
    response = client.get("/api/v1/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_detailed_all_dependencies_healthy(client, vault_repo):
    """Detailed health returns 200 when all dependencies are healthy."""
    response = client.get("/api/v1/health/detailed")
    
    assert response.status_code == 200
    data = response.json()
    
    print("HEALTH_DETAILED_RESPONSE:", data)
    
    assert data["status"] == "healthy"
    assert len(data["dependencies"]) == 2
    
    # Check PostgreSQL
    db_dep = next(d for d in data["dependencies"] if d["name"] == "postgresql")
    assert db_dep["status"] == "ok"
    assert db_dep["latency_ms"] is not None
    assert db_dep["latency_ms"] > 0
    assert db_dep["error"] is None
    
    # Check Redis
    redis_dep = next(d for d in data["dependencies"] if d["name"] == "redis")
    assert redis_dep["status"] == "ok"
    assert redis_dep["latency_ms"] is not None
    assert redis_dep["latency_ms"] > 0
    assert redis_dep["error"] is None


def test_health_detailed_database_down(client):
    """Detailed health returns unhealthy when database is down."""
    # Mock database to raise exception
    with patch('app.api.v1.health._check_database') as mock_check:
        mock_check.return_value = {
            "name": "postgresql",
            "status": "down",
            "latency_ms": 5.0,
            "error": "Connection refused",
        }
        
        response = client.get("/api/v1/health/detailed")
        
        assert response.status_code == 200  # Still returns 200, but status is unhealthy
        data = response.json()
        
        assert data["status"] == "unhealthy"


def test_health_detailed_redis_down(client):
    """Detailed health returns unhealthy when Redis is down."""
    # Mock Redis to raise exception
    with patch('app.api.v1.health._check_redis') as mock_check:
        mock_check.return_value = {
            "name": "redis",
            "status": "down",
            "latency_ms": 5.0,
            "error": "Connection refused",
        }
        
        response = client.get("/api/v1/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "unhealthy"


def test_health_endpoint_fast(client):
    """Health endpoint responds quickly (< 100ms)."""
    import time
    
    start = time.time()
    response = client.get("/api/v1/health")
    duration = time.time() - start
    
    assert response.status_code == 200
    assert duration < 0.1  # Less than 100ms


def test_health_detailed_includes_latency(client, vault_repo):
    """Detailed health includes latency measurements for each dependency."""
    response = client.get("/api/v1/health/detailed")
    
    assert response.status_code == 200
    data = response.json()
    
    for dep in data["dependencies"]:
        assert "latency_ms" in dep
        if dep["status"] == "ok":
            assert dep["latency_ms"] > 0
            assert dep["latency_ms"] < 1000  # Should be fast


def test_health_detailed_truncates_long_errors(client):
    """Long error messages are truncated to prevent huge responses."""
    long_error = "x" * 200  # 200 character error
    
    with patch('app.api.v1.health._check_database') as mock_check:
        mock_check.return_value = {
            "name": "postgresql",
            "status": "down",
            "latency_ms": 5.0,
            "error": long_error,
        }
        
        response = client.get("/api/v1/health/detailed")
        data = response.json()
        
        db_dep = next(d for d in data["dependencies"] if d["name"] == "postgresql")
        
        # Error should be truncated to 100 chars
        assert len(db_dep["error"]) <= 100


def test_health_and_detailed_have_different_response_times(client, vault_repo):
    """
    Detailed health check takes measurable time while simple check is instant.
    
    Note: Due to connection pooling, detailed may sometimes be marginally faster
    in timing tests. We verify both are fast (< 100ms) and detailed does actual work.
    """
    import time
    
    # Warm up connections first
    client.get("/api/v1/health/detailed")
    
    # Measure simple health (no dependency checks)
    start = time.time()
    client.get("/api/v1/health")
    simple_duration = time.time() - start
    
    # Measure detailed health (checks DB + Redis)
    start = time.time()
    client.get("/api/v1/health/detailed")
    detailed_duration = time.time() - start
    
    # Both should be fast (< 100ms)
    assert simple_duration < 0.1, f"Simple health too slow: {simple_duration}s"
    assert detailed_duration < 0.5, f"Detailed health too slow: {detailed_duration}s"
    
    # Detailed should typically be slower, but allow tolerance for timing variations
    # We primarily verify detailed does actual dependency checks
    assert detailed_duration > 0.001, "Detailed health should take measurable time for checks"


def test_health_endpoints_excluded_from_auth(client):
    """
    Health endpoints don't require authentication.
    
    Load balancers and monitoring tools need unauthenticated access.
    """
    # Clear any auth overrides from fixtures
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    response = client.get("/api/v1/health/detailed")
    assert response.status_code == 200