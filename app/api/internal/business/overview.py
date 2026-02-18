from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.infrastructure.db.queries.business_metrics import (
    get_member_metrics,
    get_user_metrics,
    get_vault_metrics,
)
from app.api.deps.db import get_db

router = APIRouter()


# =============================================================================
# RESPONSE SCHEMAS (scoped to this endpoint)
# =============================================================================

class UserOverview(BaseModel):
    """User count summary."""
    total: int
    new_today: int
    new_this_week: int


class VaultOverview(BaseModel):
    """Vault count summary."""
    total: int
    with_pin: int
    by_status: dict[str, int]


class MemberOverview(BaseModel):
    """Vault authorization summary."""
    total_authorizations: int
    by_role: dict[str, int]


class BusinessOverviewResponse(BaseModel):
    """Full business overview response."""
    generated_at: datetime
    users: UserOverview
    vaults: VaultOverview
    members: MemberOverview


# =============================================================================
# ENDPOINT
# =============================================================================

@router.get(
    "/overview",
    response_model=BusinessOverviewResponse,
    summary="Business metrics overview",
)
def get_business_overview(
    db: Annotated[Session, Depends(get_db)],
) -> BusinessOverviewResponse:
    """
    Aggregated business metrics from the database.

    Returns counts for users, vaults, and vault members.
    Data is queried live on each request (no caching yet).

    Authentication:
        Requires X-Admin-Token header (enforced by parent router).
    """
    user_metrics = get_user_metrics(db)
    vault_metrics = get_vault_metrics(db)
    member_metrics = get_member_metrics(db)

    return BusinessOverviewResponse(
        generated_at=datetime.now(timezone.utc),
        users=UserOverview(
            total=user_metrics.total,
            new_today=user_metrics.new_today,
            new_this_week=user_metrics.new_this_week,
        ),
        vaults=VaultOverview(
            total=vault_metrics.total,
            with_pin=vault_metrics.with_pin,
            by_status=vault_metrics.by_status,
        ),
        members=MemberOverview(
            total_authorizations=member_metrics.total_authorizations,
            by_role=member_metrics.by_role,
        ),
    )