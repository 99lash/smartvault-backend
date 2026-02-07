from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps.common import get_current_user_id
from app.api.deps.users import get_current_user
from app.api.deps.vaults import (
    get_check_vault_access_uc,
    get_send_unlock_command_uc,
    get_vault_repo,
)
from app.application.ports.vault_repository import VaultRepository
from app.application.use_cases.check_vault_access import CheckVaultAccess
from app.application.use_cases.get_vault_status import GetVaultStatus, GetVaultStatusInput
from app.application.use_cases.provision_vault import (
    HardwareAlreadyProvisioned,
    ProvisionVault,
)
from app.application.use_cases.send_unlock_command import SendUnlockCommand, VaultOfflineError
from app.domain.exceptions import (
    InsufficientPermissionsError,
    UnauthorizedVaultAccessError,
    VaultNotFoundError,
)
from app.domain.models.user import User
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
