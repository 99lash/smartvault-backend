from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_vault_repo
from app.application.services.vault_repository import VaultRepository
from app.application.use_cases.get_vault_status import GetVaultStatus
from app.schemas.vaults import VaultStatusResponse


router = APIRouter(tags=["vaults"])


@router.get("/vaults/{vault_id}/status", response_model=VaultStatusResponse)
def get_vault_status(
    vault_id: str,
    repo: VaultRepository = Depends(get_vault_repo),
) -> VaultStatusResponse:
    use_case = GetVaultStatus(repo)
    result = use_case.execute(vault_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Vault not found")

    v = result.vault
    return VaultStatusResponse(vault_id=v.id, status=v.status, last_seen_at=v.last_seen_at)
