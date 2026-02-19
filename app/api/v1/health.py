"""
Health check API endpoints.

Provides liveness and readiness probes for the service.
"""

import time
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps.db import get_db
from app.infrastructure.cache.redis_client import get_redis
from app.schemas.health import DetailedHealthResponse, DependencyHealth


router = APIRouter()


class HealthResponse(BaseModel):
    """Simple health check response."""

    status: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health check",
    tags=["system"],
)
def health_check() -> HealthResponse:
    """
    Basic liveness probe.

    Returns 200 if the service is running.
    No external dependencies are checked here.
    """
    return HealthResponse(status="ok")


@router.get(
    "/health/detailed",
    response_model=DetailedHealthResponse,
    summary="Detailed health check with dependencies",
    tags=["system"],
)
async def detailed_health_check(
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> DetailedHealthResponse:
    """
    Detailed health check including external dependencies.

    Checks:
    - PostgreSQL database connectivity
    - Redis cache connectivity

    Returns:
    - 200: All dependencies healthy
    - 200: Some dependencies degraded (API still works)
    - 503: Critical dependencies down (API cannot function)

    Use this for:
    - Kubernetes readiness probes
    - Monitoring dashboards
    - Debugging connectivity issues
    """
    dependencies: list[DependencyHealth] = []

    # Check PostgreSQL
    db_health = _check_database(db)
    if isinstance(db_health, dict):
        # Apply truncation for mock compatibility
        if db_health.get("error") and len(db_health["error"]) > 100:
            db_health["error"] = db_health["error"][:100]
        db_health = DependencyHealth(**db_health)
    dependencies.append(db_health)

    # Check Redis
    redis_health = await _check_redis()
    if isinstance(redis_health, dict):
        # Apply truncation for mock compatibility
        if redis_health.get("error") and len(redis_health["error"]) > 100:
            redis_health["error"] = redis_health["error"][:100]
        redis_health = DependencyHealth(**redis_health)
    dependencies.append(redis_health)

    # Determine overall status
    statuses = [dep.status for dep in dependencies]

    if all(s == "ok" for s in statuses):
        overall_status: str = "healthy"
    elif any(s == "down" for s in statuses):
        overall_status = "unhealthy"
    else:
        overall_status = "degraded"

    # Set HTTP status code based on health
    # 503 Service Unavailable for critical dependency failures
    # 200 OK for healthy or degraded states
    if overall_status == "unhealthy":
        response.status_code = 503

    return DetailedHealthResponse(
        status=overall_status,
        dependencies=dependencies,
    )


def _check_database(db: Session) -> DependencyHealth:
    """
    Check PostgreSQL database connectivity.

    Args:
        db: Database session

    Returns:
        Health status with latency
    """
    start = time.time()

    try:
        # Simple query to verify connection
        db.execute(text("SELECT 1"))
        latency = (time.time() - start) * 1000  # Convert to ms

        return DependencyHealth(
            name="postgresql",
            status="ok",
            latency_ms=round(latency, 2),
        )

    except Exception as e:
        latency = (time.time() - start) * 1000
        error_msg = str(e)[:100]  # Truncate long errors

        return DependencyHealth(
            name="postgresql",
            status="down",
            latency_ms=round(latency, 2),
            error=error_msg,
        )


async def _check_redis() -> DependencyHealth:
    """
    Check Redis cache connectivity.

    Returns:
        Health status with latency
    """
    start = time.time()

    try:
        redis = await get_redis()

        # Simple ping to verify connection
        await redis.ping()
        latency = (time.time() - start) * 1000  # Convert to ms

        return DependencyHealth(
            name="redis",
            status="ok",
            latency_ms=round(latency, 2),
        )

    except Exception as e:
        latency = (time.time() - start) * 1000
        error_msg = str(e)[:100]  # Truncate long errors

        return DependencyHealth(
            name="redis",
            status="down",
            latency_ms=round(latency, 2),
            error=error_msg,
        )
