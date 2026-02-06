from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps.common import get_current_user_id
from app.api.deps.vaults import get_check_vault_access_uc, get_vault_repo
from app.application.ports.vault_repository import VaultRepository
from app.application.use_cases.get_vault_status import GetVaultStatus, GetVaultStatusInput
from app.application.use_cases.provision_vault import (
    HardwareAlreadyProvisioned,
    ProvisionVault,
)
from app.application.use_cases.check_vault_access import CheckVaultAccess
from app.domain.exceptions import UnauthorizedVaultAccessError
from app.schemas.vaults import (
    ProvisionVaultRequest,
    ProvisionVaultResponse,
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
    user_id: str = Depends(get_current_user_id),
) -> VaultStatusResponse:
    use_case = GetVaultStatus(repo, check_access)
    try:
        result = use_case.execute(GetVaultStatusInput(vault_id=vault_id, user_id=user_id))
    except UnauthorizedVaultAccessError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    if result is None:
        raise HTTPException(status_code=404, detail="Vault not found")

    v = result.vault
    return VaultStatusResponse(vault_id=v.id, status=v.status, last_seen_at=v.last_seen_at)
