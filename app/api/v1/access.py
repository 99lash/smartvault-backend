from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from starlette.concurrency import run_in_threadpool

from app.api.deps.auth import get_current_user_id, get_rate_limiter
from app.api.deps.users import get_user_repo
from app.api.deps.vaults import (
    get_add_vault_member_uc,
    get_list_vault_members_uc,
    get_remove_vault_member_uc,
)
from app.application.ports.user_repository import UserRepository
from app.application.use_cases.add_vault_member import AddVaultMember, AddVaultMemberInput
from app.application.use_cases.list_vault_members import ListVaultMembers
from app.application.use_cases.remove_vault_member import RemoveVaultMember, RemoveVaultMemberInput
from app.domain.exceptions import (
    CannotRemoveOwnerError,
    InsufficientPermissionsError,
    UserNotFoundError,
    UnauthorizedVaultAccessError,
    VaultNotFoundError,
)
from app.domain.value_objects.vault_role import VaultRole
from app.infrastructure.security.rate_limiter import RateLimiter
from app.schemas.access import (
    AddMemberRequest,
    MemberListResponse,
    MemberResponse,
    VaultRoleEnum,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/vaults", tags=["vault-access"])


@router.post("/{vault_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def add_vault_member(
    vault_id: str,
    payload: AddMemberRequest,
    current_user_id: str = Depends(get_current_user_id),
    user_repo: UserRepository = Depends(get_user_repo),
    uc: AddVaultMember = Depends(get_add_vault_member_uc),
    limiter: RateLimiter = Depends(get_rate_limiter),
) -> MemberResponse:
    """
    Add a member to a vault with a specific role.

    Only the vault owner can add members.
    If the user already has access, their role is updated (idempotent).
    """
    # Rate limit
    await limiter.allow_request(
        key=f"add_member:{current_user_id}",
        limit=10,
        window_seconds=60,
    )

    # Ensure target user exists for enrichment and validation
    try:
        target_user = await run_in_threadpool(user_repo.get_by_id, payload.user_id)
        if target_user is None:
            raise UserNotFoundError(payload.user_id)
    except UserNotFoundError as e:
        logger.warning("user_not_found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    try:
        domain_role = VaultRole(payload.role.value)

        result = await run_in_threadpool(
            uc.execute,
            AddVaultMemberInput(
                vault_id=vault_id,
                actor_user_id=current_user_id,
                target_user_id=payload.user_id,
                role=domain_role,
            ),
        )

        auth = result.authorization

        return MemberResponse(
            user_id=auth.user_id,
            email=target_user.email,
            full_name=target_user.full_name,
            role=VaultRoleEnum(auth.role.value),
            granted_at=auth.granted_at,
            granted_by=auth.granted_by,
        )

    except (VaultNotFoundError, UserNotFoundError) as e:
        logger.warning("resource_not_found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    except (UnauthorizedVaultAccessError, InsufficientPermissionsError) as e:
        logger.warning("access_denied")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    except ValueError as e:
        # e.g., attempting to add the owner as a member
        logger.warning("validation_error")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e))


@router.delete("/{vault_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_vault_member(
    vault_id: str,
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    uc: RemoveVaultMember = Depends(get_remove_vault_member_uc),
) -> None:
    """
    Remove a member from a vault.

    Only the vault owner can remove members.
    Idempotent: no error if member doesn't exist.
    Cannot remove the vault owner.
    """
    try:
        await run_in_threadpool(
            uc.execute,
            RemoveVaultMemberInput(
                vault_id=vault_id,
                actor_user_id=current_user_id,
                target_user_id=user_id,
            ),
        )
    except (VaultNotFoundError, UserNotFoundError) as e:
        logger.warning("resource_not_found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    except (UnauthorizedVaultAccessError, InsufficientPermissionsError) as e:
        logger.warning("access_denied")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    except CannotRemoveOwnerError as e:
        logger.warning("validation_error")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e))


@router.get("/{vault_id}/members", response_model=MemberListResponse)
async def list_vault_members(
    vault_id: str,
    current_user_id: str = Depends(get_current_user_id),
    user_repo: UserRepository = Depends(get_user_repo),
    uc: ListVaultMembers = Depends(get_list_vault_members_uc),
) -> MemberListResponse:
    """
    List all members of a vault.

    User must have access to the vault (owner or member).
    """
    try:
        result = await run_in_threadpool(uc.execute, vault_id, current_user_id)

        user_ids = [auth.user_id for auth in result.members]
        users = await run_in_threadpool(user_repo.get_by_ids, user_ids)

        members = [
            MemberResponse(
                user_id=auth.user_id,
                email=users[auth.user_id].email,
                full_name=users[auth.user_id].full_name,
                role=VaultRoleEnum(auth.role.value),
                granted_at=auth.granted_at,
                granted_by=auth.granted_by,
            )
            for auth in result.members
            if auth.user_id in users
        ]

        if len(members) != len(result.members):
            missing_ids = set(user_ids) - set(users.keys())
            logger.warning("resource_not_found", missing_user_count=len(missing_ids))
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

        return MemberListResponse(
            vault_id=vault_id,
            members=members,
        )

    except (VaultNotFoundError, UserNotFoundError) as e:
        logger.warning("resource_not_found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    except (UnauthorizedVaultAccessError, InsufficientPermissionsError) as e:
        logger.warning("access_denied")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
