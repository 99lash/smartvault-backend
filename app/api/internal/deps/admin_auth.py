from __future__ import annotations

import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.logging import get_logger
from app.core.settings import settings

logger = get_logger(__name__)

_admin_token_header = APIKeyHeader(
    name="X-Admin-Token",
    scheme_name="AdminToken",
    description="Admin API token for internal endpoints",
    auto_error=False,
)


def require_admin_token(
    token: str | None = Security(_admin_token_header),
) -> str:
    """
    Validate the X-Admin-Token header.

    Args:
        token: Token from X-Admin-Token header.

    Returns:
        The validated token string.

    Raises:
        HTTPException 503: Admin API not configured.
        HTTPException 401: Missing or invalid token.
    """
    if not token:
        logger.warning("admin_token_missing")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin token required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if not settings.ADMIN_API_TOKEN:
        logger.warning("admin_api_not_configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin API is not configured",
        )

    is_valid = secrets.compare_digest(
        token.encode("utf-8"),
        settings.ADMIN_API_TOKEN.encode("utf-8"),
    )

    if not is_valid:
        logger.warning("admin_token_invalid")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    logger.info("admin_api_accessed")
    return token
