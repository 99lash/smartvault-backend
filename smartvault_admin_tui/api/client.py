"""
HTTP client for SmartVault Internal API.

Provides async methods to call all internal endpoints.
"""
from __future__ import annotations

# ... (imports)
import logging
from typing import Any, Optional

import httpx
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type, 
    before_sleep_log
)

from smartvault_admin_tui.config import config

logger = logging.getLogger(__name__)

class APIClient:
    """Async HTTP client for internal API endpoints."""
    
    def __init__(self, base_url: str | None = None, admin_token: str | None = None, client: httpx.AsyncClient | None = None):
        self.base_url = base_url or config.api_base_url
        self.admin_token = admin_token or config.admin_token
        # Allow injecting an existing client (connection pooling)
        self._client = client
        self._own_client = False
    
    async def __aenter__(self) -> APIClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"X-Admin-Token": self.admin_token},
                timeout=30.0,
            )
            self._own_client = True
        return self
    
    async def __aexit__(self, *args) -> None:
        if self._own_client and self._client:
            await self._client.aclose()
            self._client = None
            self._own_client = False
            
    async def close(self) -> None:
        """Manual close for long-lived instances."""
        if self._own_client and self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            # Fallback for lazy initialization if needed, though explicit is better
             self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"X-Admin-Token": self.admin_token},
                timeout=30.0,
            )
             self._own_client = True
        return self._client
    
    # =========================================================================
    # PING
    # =========================================================================
    
    @retry(
        retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def ping(self) -> dict[str, Any]:
        """Admin API connectivity check."""
        response = await self.client.get("/internal/ping")
        response.raise_for_status()
        return response.json()
    
    # =========================================================================
    # DASHBOARD & SUMMARY
    # =========================================================================
    
    async def get_ops_summary(self) -> dict[str, Any]:
        """Complete ops dashboard summary."""
        response = await self.client.get("/internal/ops/summary")
        response.raise_for_status()
        return response.json()
    
    async def get_business_overview(self) -> dict[str, Any]:
        """Business metrics overview."""
        response = await self.client.get("/internal/business/overview")
        response.raise_for_status()
        return response.json()
    
    # =========================================================================
    # SECURITY
    # =========================================================================
    
    async def get_security_alerts(self) -> dict[str, Any]:
        """Security alerts and suspicious activity."""
        response = await self.client.get("/internal/security/alerts")
        response.raise_for_status()
        return response.json()
    
    # =========================================================================
    # ACTIVITY
    # =========================================================================
    
    async def get_activity(
        self, 
        hours: int = 24, 
        limit: int = 50
    ) -> dict[str, Any]:
        """Recent activity log."""
        response = await self.client.get(
            "/internal/business/activity",
            params={"hours": hours, "limit": limit}
        )
        response.raise_for_status()
        return response.json()
    
    # =========================================================================
    # RATE LIMITS
    # =========================================================================
    
    async def get_rate_limits(self) -> dict[str, Any]:
        """Rate limiting dashboard."""
        response = await self.client.get("/internal/ops/rate-limits")
        response.raise_for_status()
        return response.json()
    
    # =========================================================================
    # SESSIONS
    # =========================================================================
    
    async def get_session_stats(self) -> dict[str, Any]:
        """Refresh token session statistics."""
        response = await self.client.get("/internal/ops/sessions/stats")
        response.raise_for_status()
        return response.json()
    
    async def revoke_user_sessions(self, user_id: str) -> dict[str, Any]:
        """Revoke all sessions for a user."""
        response = await self.client.delete(f"/internal/ops/sessions/{user_id}")
        response.raise_for_status()
        return response.json()
    
    # =========================================================================
    # NOTIFICATIONS
    # =========================================================================
    
    async def get_email_status(self) -> dict[str, Any]:
        """Email service status and daily send counts."""
        response = await self.client.get("/internal/ops/notifications/email")
        response.raise_for_status()
        return response.json()
    
    # =========================================================================
    # DIAGNOSTICS
    # =========================================================================
    
    async def get_redis_diagnostics(self) -> dict[str, Any]:
        """Redis health and statistics."""
        response = await self.client.get("/internal/ops/diagnostics/redis")
        response.raise_for_status()
        return response.json()
    
    async def get_websocket_diagnostics(self) -> dict[str, Any]:
        """WebSocket connection statistics."""
        response = await self.client.get("/internal/ops/diagnostics/websockets")
        response.raise_for_status()
        return response.json()
    
    async def get_database_diagnostics(self) -> dict[str, Any]:
        """Database connection pool statistics."""
        response = await self.client.get("/internal/ops/diagnostics/database")
        response.raise_for_status()
        return response.json()
    
    # =========================================================================
    # AUDIT LOGS
    # =========================================================================
    
    async def get_audit_logs(
        self,
        page: int = 1,
        limit: int = 50,
        action: str | None = None
    ) -> dict[str, Any]:
        """Admin audit logs."""
        params: dict[str, str | int] = {"page": page, "limit": limit}
        if action:
            params["action"] = action
        response = await self.client.get("/internal/ops/audit", params=params)
        response.raise_for_status()
        return response.json()
    
    # =========================================================================
    # API KEYS
    # =========================================================================
    
    async def list_api_keys(self, active_only: bool = True) -> dict[str, Any]:
        """List API keys."""
        response = await self.client.get(
            "/internal/ops/api-keys",
            params={"active_only": str(active_only).lower()}
        )
        response.raise_for_status()
        return response.json()
    
    async def create_api_key(
        self,
        name: str,
        expires_in_days: int | None = None
    ) -> dict[str, Any]:
        """Create a new API key."""
        payload: dict[str, str | int] = {"name": name}
        if expires_in_days is not None:
            payload["expires_in_days"] = expires_in_days
        response = await self.client.post("/internal/ops/api-keys", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def revoke_api_key(self, key_id: int) -> bool:
        """Revoke an API key."""
        response = await self.client.delete(f"/internal/ops/api-keys/{key_id}")
        response.raise_for_status()
        return response.status_code == 204
    
# =========================================================================
# BUSINESS TRENDS
# =========================================================================

    async def get_business_trends(self, days: int = 30) -> dict[str, Any]:
        """Daily user signup and vault provisioning trends."""
        response = await self.client.get(
            "/internal/business/trends",
            params={"days": days},
        )
        response.raise_for_status()
        return response.json()
