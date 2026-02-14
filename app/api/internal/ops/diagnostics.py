"""
Internal ops diagnostics endpoints.

Endpoints:
    GET /api/internal/ops/diagnostics/redis
    GET /api/internal/ops/diagnostics/websockets
    GET /api/internal/ops/diagnostics/database

Clean Architecture:
    API layer only. Uses infrastructure queries (Redis, DB) and messaging manager.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.infrastructure.db.session import get_db
from app.infrastructure.db.queries import system_metrics
from app.infrastructure.messaging import websocket_manager

router = APIRouter()


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class RedisDiagnosticsResponse(BaseModel):
    status: str
    connected: bool
    memory_used_mb: float
    total_keys: int
    uptime_seconds: int
    checked_at: datetime


class WebSocketDiagnosticsResponse(BaseModel):
    total_users: int
    total_user_connections: int
    total_vaults: int
    subscriptions: int
    online_vaults: list[str]
    checked_at: datetime


class DatabaseDiagnosticsResponse(BaseModel):
    status: str
    pool_size: int
    checked_out: int
    overflow: int
    checked_at: datetime


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get(
    "/diagnostics/redis",
    response_model=RedisDiagnosticsResponse,
    summary="Redis health and statistics",
)
async def get_redis_diagnostics() -> RedisDiagnosticsResponse:
    metrics = await system_metrics.get_redis_health()
    return RedisDiagnosticsResponse(
        status=metrics.status,
        connected=metrics.connected,
        memory_used_mb=round(metrics.memory_used_mb, 2),
        total_keys=metrics.total_keys,
        uptime_seconds=metrics.uptime_seconds,
        checked_at=datetime.now(timezone.utc),
    )


@router.get(
    "/diagnostics/websockets",
    response_model=WebSocketDiagnosticsResponse,
    summary="WebSocket connection statistics",
)
def get_websocket_diagnostics() -> WebSocketDiagnosticsResponse:
    stats = websocket_manager.manager.get_connection_stats()
    online = websocket_manager.manager.get_online_vaults()
    return WebSocketDiagnosticsResponse(
        total_users=stats.get("total_users", 0),
        total_user_connections=stats.get("total_user_connections", 0),
        total_vaults=stats.get("total_vaults", 0),
        subscriptions=stats.get("subscriptions", 0),
        online_vaults=online,
        checked_at=datetime.now(timezone.utc),
    )


@router.get(
    "/diagnostics/database",
    response_model=DatabaseDiagnosticsResponse,
    summary="Database connection pool statistics",
)
def get_database_diagnostics(
    db: Session = Depends(get_db),
) -> DatabaseDiagnosticsResponse:
    metrics = system_metrics.get_database_pool_metrics(db)
    return DatabaseDiagnosticsResponse(
        status=metrics.status,
        pool_size=metrics.pool_size,
        checked_out=metrics.checked_out,
        overflow=metrics.overflow,
        checked_at=datetime.now(timezone.utc),
    )
