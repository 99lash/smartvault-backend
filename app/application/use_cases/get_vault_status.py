from dataclasses import dataclass

from app.application.ports.vault_repository import VaultRepository
from app.application.use_cases.check_vault_access import CheckVaultAccess
from app.domain.exceptions import UnauthorizedVaultAccessError
from app.domain.models.vault import Vault


@dataclass(frozen=True)
class GetVaultStatusResult:
    vault: Vault


@dataclass(frozen=True)
class GetVaultStatusInput:
    vault_id: str
    user_id: str


class GetVaultStatus:
    def __init__(self, repo: VaultRepository, check_access: CheckVaultAccess) -> None:
        self._repo = repo
        self._check_access = check_access

    def execute(self, inp: GetVaultStatusInput) -> GetVaultStatusResult | None:
        vault = self._repo.get_by_id(inp.vault_id)
        if vault is None:
            return None

        access_info = self._check_access.execute(inp.vault_id, inp.user_id)
        if not access_info.has_access:
            raise UnauthorizedVaultAccessError(inp.user_id, inp.vault_id)

        return GetVaultStatusResult(vault=vault)
