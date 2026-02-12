"""
Tests for the /metrics Prometheus endpoint.

Verifies that the endpoint is accessible and returns
Prometheus-formatted metrics.
"""

import pytest


def test_metrics_endpoint_accessible(client):
    """Metrics endpoint returns 200."""
    response = client.get("/metrics")

    assert response.status_code == 200


def test_metrics_endpoint_returns_prometheus_format(client):
    """Metrics endpoint returns Prometheus text format."""
    response = client.get("/metrics")

    content_type = response.headers.get("content-type", "")
    assert "text/plain" in content_type


def test_metrics_endpoint_contains_http_metrics(client):
    """HTTP request metrics are present after making requests."""
    # Make a request to generate HTTP metrics
    client.get("/api/v1/health")

    # Check /metrics contains HTTP metrics
    response = client.get("/metrics")
    content = response.text

    assert "http_requests_total" in content


def test_metrics_endpoint_contains_app_info(client):
    """App info metric is present."""
    response = client.get("/metrics")
    content = response.text

    assert "smartvault_app_info" in content


def test_metrics_endpoint_not_in_openapi_schema(client):
    """Metrics endpoint is excluded from public API docs."""
    response = client.get("/openapi.json")
    schema = response.json()

    assert "/metrics" not in schema.get("paths", {})


def test_health_endpoint_not_tracked_in_metrics(client):
    """Health check requests are excluded from HTTP metrics tracking."""
    # Make several health check requests
    for _ in range(3):
        client.get("/api/v1/health")

    response = client.get("/metrics")
    content = response.text

    # Health endpoint should be excluded
    assert 'handler="/api/v1/health"' not in content