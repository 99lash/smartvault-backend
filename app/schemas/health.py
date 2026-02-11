"""
Health check schemas for API responses.

These schemas define the response models for health check endpoints.
"""

from typing import Literal
from pydantic import BaseModel


class DependencyHealth(BaseModel):
    """Health status of a single dependency (e.g., PostgreSQL, Redis)."""

    name: str
    status: Literal["ok", "down", "degraded"]
    latency_ms: float
    error: str | None = None


class DetailedHealthResponse(BaseModel):
    """Detailed health check response with dependency statuses."""

    status: Literal["healthy", "unhealthy", "degraded"]
    dependencies: list[DependencyHealth]
