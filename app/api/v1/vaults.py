from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from starlette.concurrency import run_in_threadpool

from app.api.deps.auth import get_current_user_id, get_rate_limiter
from app.api.deps.users import get_current_user
from app.api.deps.vaults import (
    get_check_vault_access_uc,
    get_remove_vault_pin_uc,
    get_send_unlock_command_uc,
    get_set_vault_pin_uc,
    get_unlock_with_pin_uc,
    get_vault_repo,
)
from app.application.ports.vault_repository import VaultRepository
from app.application.use_cases.check_vault_access import CheckVaultAccess
from app.application.use_cases.get_vault_status import GetVaultStatus, GetVaultStatusInput
from app.application.use_cases.provision_vault import (
    HardwareAlreadyProvisioned,
    ProvisionVault,
)
from app.application.use_cases.remove_vault_pin import RemoveVaultPIN, RemoveVaultPINInput
from app.application.use_cases.send_unlock_command import SendUnlockCommand, VaultOfflineError
from app.application.use_cases.set_vault_pin import SetVaultPIN, SetVaultPINInput
from app.application.use_cases.unlock_vault_with_pin import (
    UnlockVaultWithPIN,
    UnlockVaultWithPINInput,
)
from app.domain.exceptions import (
    InsufficientPermissionsError,
    InvalidPINError,
    PINLockedOutError,
    PINNotSetError,
    UnauthorizedVaultAccessError,
    VaultNotFoundError,
)
from app.domain.models.user import User
from app.infrastructure.security.rate_limiter import RateLimiter
from app.schemas.pin import (
    PINStatusResponse,
    RemovePINResponse,
    SetPINRequest,
    SetPINResponse,
    UnlockWithPINRequest,
    UnlockWithPINResponse,
)
from app.schemas.vaults import (
    ProvisionVaultRequest,
    ProvisionVaultResponse,
    UnlockCommandResponse,
    VaultStatusResponse,
)


router = APIRouter(tags=["vaults"])


@router.post(
    "/vaults/provision",
    response_model=ProvisionVaultResponse,
    status_code=status.HTTP_201_CREATED,
)
def provision_vault(
    payload: ProvisionVaultRequest,
    owner_id: str = Depends(get_current_user_id),
    repo: VaultRepository = Depends(get_vault_repo),
) -> ProvisionVaultResponse:
    use_case = ProvisionVault(repo)
    try:
        result = use_case.execute(
            owner_id=owner_id,
            hardware_uuid=payload.hardware_uuid,
            vault_name=payload.vault_name,
        )
    except HardwareAlreadyProvisioned:
        raise HTTPException(status_code=409, detail="Hardware already provisioned")

    v = result.vault
    return ProvisionVaultResponse(
        vault_id=v.id,
        hardware_uuid=v.hardware_uuid,
        vault_name=v.vault_name,
        status=v.status,
    )


@router.get("/vaults/{vault_id}/status", response_model=VaultStatusResponse)
def get_vault_status(
    vault_id: str,
    repo: VaultRepository = Depends(get_vault_repo),
    check_access: CheckVaultAccess = Depends(get_check_vault_access_uc),
    current_user: User = Depends(get_current_user),
) -> VaultStatusResponse:
    use_case = GetVaultStatus(repo, check_access)
    try:
        result = use_case.execute(
            GetVaultStatusInput(vault_id=vault_id, user_id=current_user.id)
        )
    except UnauthorizedVaultAccessError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except VaultNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vault not found")

    if result is None:
        raise HTTPException(status_code=404, detail="Vault not found")

    v = result.vault
    return VaultStatusResponse(vault_id=v.id, status=v.status, last_seen_at=v.last_seen_at)


@router.post(
    "/vaults/{vault_id}/unlock",
    response_model=UnlockCommandResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def send_unlock_command(
    vault_id: str,
    uc: SendUnlockCommand = Depends(get_send_unlock_command_uc),
    current_user: User = Depends(get_current_user),
) -> UnlockCommandResponse:
    try:
        result = await uc.execute(vault_id=vault_id, user_id=current_user.id)
    except UnauthorizedVaultAccessError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except InsufficientPermissionsError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vault not found")
    except VaultOfflineError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    return UnlockCommandResponse(
        command_id=result.command_id,
        vault_id=result.vault_id,
        expires_at=result.expires_at,
        sent=result.sent,
    )


@router.post(
    "/vaults/{vault_id}/pin",
    response_model=SetPINResponse,
    status_code=status.HTTP_201_CREATED,
)
async def set_vault_pin(
    vault_id: str,
    payload: SetPINRequest,
    current_user_id: str = Depends(get_current_user_id),
    check_access: CheckVaultAccess = Depends(get_check_vault_access_uc),
    uc: SetVaultPIN = Depends(get_set_vault_pin_uc),
    limiter: RateLimiter = Depends(get_rate_limiter),
) -> SetPINResponse:
    await limiter.allow_request(
        key=f"pin:set:{current_user_id}:{vault_id}",
        limit=10,
        window_seconds=60,
    )

    try:
        access = await run_in_threadpool(check_access.execute, vault_id, current_user_id)
        if not access.has_access or (access.role and not access.role.can_unlock()):
            raise UnauthorizedVaultAccessError(current_user_id, vault_id)

        result = await run_in_threadpool(
            uc.execute,
            SetVaultPINInput(vault_id=vault_id, pin=payload.pin, user_id=current_user_id),
        )
        return SetPINResponse(vault_id=result.vault.id, pin_set_at=result.vault.pin_set_at)
    except UnauthorizedVaultAccessError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except VaultNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vault not found")
    except InvalidPINError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e))


@router.delete(
    "/vaults/{vault_id}/pin",
    response_model=RemovePINResponse,
    status_code=status.HTTP_200_OK,
)
async def remove_vault_pin(
    vault_id: str,
    current_user_id: str = Depends(get_current_user_id),
    check_access: CheckVaultAccess = Depends(get_check_vault_access_uc),
    uc: RemoveVaultPIN = Depends(get_remove_vault_pin_uc),
    limiter: RateLimiter = Depends(get_rate_limiter),
) -> RemovePINResponse:
    await limiter.allow_request(
        key=f"pin:remove:{current_user_id}:{vault_id}",
        limit=10,
        window_seconds=60,
    )

    try:
        access = await run_in_threadpool(check_access.execute, vault_id, current_user_id)
        if not access.has_access or (access.role and not access.role.can_unlock()):
            raise UnauthorizedVaultAccessError(current_user_id, vault_id)

        result = await run_in_threadpool(
            uc.execute,
            RemoveVaultPINInput(vault_id=vault_id, user_id=current_user_id),
        )
        return RemovePINResponse(vault_id=result.vault.id, removed=True)
    except UnauthorizedVaultAccessError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except VaultNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vault not found")
    except PINNotSetError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/vaults/{vault_id}/pin/status",
    response_model=PINStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_pin_status(
    vault_id: str,
    current_user_id: str = Depends(get_current_user_id),
    check_access: CheckVaultAccess = Depends(get_check_vault_access_uc),
    repo: VaultRepository = Depends(get_vault_repo),
) -> PINStatusResponse:
    try:
        access = await run_in_threadpool(check_access.execute, vault_id, current_user_id)
        if not access.has_access:
            raise UnauthorizedVaultAccessError(current_user_id, vault_id)

        vault = await run_in_threadpool(repo.get_by_id, vault_id)
        if vault is None:
            raise VaultNotFoundError(vault_id)

        return PINStatusResponse(
            vault_id=vault.id,
            is_set=vault.pin_hash is not None,
            pin_set_at=vault.pin_set_at,
        )
    except UnauthorizedVaultAccessError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except VaultNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vault not found")


@router.post(
    "/vaults/{vault_id}/unlock/pin",
    response_model=UnlockWithPINResponse,
    status_code=status.HTTP_200_OK,
)
async def unlock_vault_with_pin(
    vault_id: str,
    payload: UnlockWithPINRequest,
    current_user_id: str = Depends(get_current_user_id),
    check_access: CheckVaultAccess = Depends(get_check_vault_access_uc),
    uc: UnlockVaultWithPIN = Depends(get_unlock_with_pin_uc),
    limiter: RateLimiter = Depends(get_rate_limiter),
) -> UnlockWithPINResponse:
    await limiter.allow_request(
        key=f"pin:unlock:{current_user_id}:{vault_id}",
        limit=15,
        window_seconds=60,
    )

    try:
        access = await run_in_threadpool(check_access.execute, vault_id, current_user_id)
        if not access.has_access or (access.role and not access.role.can_unlock()):
            raise UnauthorizedVaultAccessError(current_user_id, vault_id)

        result = await uc.execute(
            UnlockVaultWithPINInput(vault_id=vault_id, pin=payload.pin, user_id=current_user_id)
        )

        return UnlockWithPINResponse(
            vault_id=result.vault.id,
            result=result.result,
            attempts_remaining=result.attempts_remaining,
        )
    except UnauthorizedVaultAccessError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except VaultNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vault not found")
    except PINNotSetError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except PINLockedOutError as e:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=str(e))
    except InvalidPINError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

