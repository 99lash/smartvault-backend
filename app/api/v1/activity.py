from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from starlette.concurrency import run_in_threadpool

from app.api.deps.auth import get_current_user_id
from app.api.deps.vaults import get_check_vault_access_uc
from app.api.deps.activity import get_activity_log_repo
from app.application.ports.activity_log_repository import ActivityLogRepository
from app.application.use_cases.check_vault_access import CheckVaultAccess
from app.domain.exceptions import UnauthorizedVaultAccessError, VaultNotFoundError
from app.domain.models.access_log import AccessLog
from app.schemas.activity import ActivityLogEntry, ActivityLogResponse

router = APIRouter(tags=["activity"])


@router.get("/vaults/{vault_id}/activity", response_model=ActivityLogResponse)
async def get_vault_activity(
    vault_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    current_user_id: str = Depends(get_current_user_id),
    check_access: CheckVaultAccess = Depends(get_check_vault_access_uc),
    repo: ActivityLogRepository = Depends(get_activity_log_repo),
) -> ActivityLogResponse:
    """Get activity log entries for a vault."""
    # Check access first
    try:
        access = await run_in_threadpool(check_access.execute, vault_id, current_user_id)
        if not access.has_access:
            raise UnauthorizedVaultAccessError(current_user_id, vault_id)
    except VaultNotFoundError:
        # Return 403 to hide vault existence (no access = no access)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Fetch logs
    logs: list[AccessLog] = await run_in_threadpool(repo.list_by_vault, vault_id, limit=limit)
    entries = [ActivityLogEntry.model_validate(log) for log in logs]

    return ActivityLogResponse(
        vault_id=vault_id,
        entries=entries,
        count=len(entries),
    )
