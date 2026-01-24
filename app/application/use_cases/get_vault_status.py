from dataclasses import dataclass
from app.application.ports.vault_repository import VaultRepository
from app.domain.models.vault import Vault


@dataclass(frozen=True)
class GetVaultStatusResult:
    vault: Vault


class GetVaultStatus:
    def __init__(self, repo: VaultRepository) -> None:
        self._repo = repo

    def execute(self, vault_id: str) -> GetVaultStatusResult | None:
        vault = self._repo.get_by_id(vault_id)
        if vault is None:
            return None
        return GetVaultStatusResult(vault=vault)
