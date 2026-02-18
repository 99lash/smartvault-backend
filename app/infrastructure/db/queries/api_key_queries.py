"""
API key database queries.

Follows activity_queries.py and audit_queries.py patterns:
- Frozen dataclass result types
- SQLAlchemy Core selects
- No domain model mapping

Clean Architecture:
    Infrastructure layer — database queries only.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.db.models.api_key_orm import APIKeyORM
from app.infrastructure.security.api_key_hasher import generate_api_key, hash_api_key


# =============================================================================
# RESULT DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class APIKeyEntry:
    """API key metadata (never contains the plain key)."""
    id: int
    name: str
    created_by: str
    last_used_at: datetime | None
    expires_at: datetime | None
    is_active: bool
    created_at: datetime


@dataclass(frozen=True)
class CreatedAPIKey:
    """Result of key creation — includes the plain key shown once."""
    id: int
    key: str          # Plain key — show once, never store
    name: str
    expires_at: datetime | None


# =============================================================================
# QUERY FUNCTIONS
# =============================================================================

def list_api_keys(db: Session, *, active_only: bool = True) -> list[APIKeyEntry]:
    """
    List API keys, optionally filtering to active only.

    Args:
        db:          SQLAlchemy session.
        active_only: When True, only return is_active=True keys.

    Returns:
        List of APIKeyEntry ordered newest first.
    """
    stmt = select(APIKeyORM).order_by(APIKeyORM.created_at.desc())

    if active_only:
        stmt = stmt.where(APIKeyORM.is_active.is_(True))

    rows = db.scalars(stmt).all()

    return [
        APIKeyEntry(
            id=row.id,
            name=row.name,
            created_by=row.created_by,
            last_used_at=row.last_used_at,
            expires_at=row.expires_at,
            is_active=row.is_active,
            created_at=row.created_at,
        )
        for row in rows
    ]


def create_api_key(
    db: Session,
    *,
    name: str,
    created_by: str,
    expires_in_days: int | None = None,
) -> CreatedAPIKey:
    """
    Generate and persist a new API key.

    The plain key is returned once and never stored — only its hash
    is persisted. The caller must show the key to the user immediately.

    Args:
        db:              SQLAlchemy session.
        name:            Human-readable label for the key.
        created_by:      Identifier of the admin creating the key.
        expires_in_days: Optional expiration in days from now.

    Returns:
        CreatedAPIKey with the plain key (show once only).
    """
    plain_key = generate_api_key()
    key_hash  = hash_api_key(plain_key)

    expires_at = None
    if expires_in_days is not None:
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

    row = APIKeyORM(
        key_hash=key_hash,
        name=name,
        created_by=created_by,
        expires_at=expires_at,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return CreatedAPIKey(
        id=row.id,
        key=plain_key,
        name=row.name,
        expires_at=row.expires_at,
    )


def revoke_api_key(db: Session, *, key_id: int) -> bool:
    """
    Deactivate an API key by setting is_active=False.

    Does not delete the row — preserves audit trail.

    Args:
        db:     SQLAlchemy session.
        key_id: Primary key of the API key to revoke.

    Returns:
        True if found and revoked, False if not found.
    """
    row = db.get(APIKeyORM, key_id)

    if row is None:
        return False

    row.is_active = False
    db.commit()
    return True
