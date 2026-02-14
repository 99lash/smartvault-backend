"""
API key management endpoints.

Endpoints:
    GET    /api/internal/ops/api-keys
    POST   /api/internal/ops/api-keys
    DELETE /api/internal/ops/api-keys/{key_id}

Clean Architecture:
    API layer — calls infrastructure queries directly.
    No application layer needed (no domain logic, straight CRUD).
"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.infrastructure.db.queries.api_key_queries import (
    create_api_key,
    list_api_keys,
    revoke_api_key,
)
from app.infrastructure.db.session import get_db

router = APIRouter()

# Sentinel for created_by when no user identity is available.
# The internal API authenticates with a shared X-Admin-Token,
# not individual user accounts.
_ADMIN_CONSOLE = "admin_console"


# =============================================================================
# REQUEST / RESPONSE SCHEMAS
# =============================================================================

class APIKeyItem(BaseModel):
    id: int
    name: str
    created_by: str
    last_used_at: datetime | None
    expires_at: datetime | None
    is_active: bool
    created_at: datetime


class APIKeysListResponse(BaseModel):
    items: list[APIKeyItem]


class CreateAPIKeyRequest(BaseModel):
    name: str
    expires_in_days: int | None = None


class CreatedAPIKeyResponse(BaseModel):
    id: int
    key: str      # Shown once only — admin must copy immediately
    name: str
    expires_at: datetime | None


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get(
    "/api-keys",
    response_model=APIKeysListResponse,
    summary="List API keys",
)
def list_api_keys_endpoint(
    db: Annotated[Session, Depends(get_db)],
    active_only: bool = True,
) -> APIKeysListResponse:
    """
    List all API keys.

    Query params:
        active_only: When true (default), only active keys are returned.

    Authentication:
        Requires X-Admin-Token header (enforced by parent router).
    """
    keys = list_api_keys(db, active_only=active_only)

    return APIKeysListResponse(
        items=[
            APIKeyItem(
                id=k.id,
                name=k.name,
                created_by=k.created_by,
                last_used_at=k.last_used_at,
                expires_at=k.expires_at,
                is_active=k.is_active,
                created_at=k.created_at,
            )
            for k in keys
        ]
    )


@router.post(
    "/api-keys",
    response_model=CreatedAPIKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new API key",
)
def create_api_key_endpoint(
    request: CreateAPIKeyRequest,
    db: Annotated[Session, Depends(get_db)],
) -> CreatedAPIKeyResponse:
    """
    Create a new API key.

    ⚠️ The plain key is returned once only. Copy it immediately —
    it cannot be recovered after this response.

    Authentication:
        Requires X-Admin-Token header (enforced by parent router).
    """
    result = create_api_key(
        db,
        name=request.name,
        created_by=_ADMIN_CONSOLE,
        expires_in_days=request.expires_in_days,
    )

    return CreatedAPIKeyResponse(
        id=result.id,
        key=result.key,
        name=result.name,
        expires_at=result.expires_at,
    )


@router.delete(
    "/api-keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke an API key",
)
def revoke_api_key_endpoint(
    key_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """
    Revoke an API key by ID.

    Sets is_active=False. The row is kept for audit purposes.

    Args:
        key_id: Primary key of the API key to revoke.

    Authentication:
        Requires X-Admin-Token header (enforced by parent router).
    """
    found = revoke_api_key(db, key_id=key_id)

    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key {key_id} not found.",
        )
