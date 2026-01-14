from datetime import datetime, timezone
from app.application.services.vault_repository import VaultRepository
from app.domain.models.vault import Vault
from app.domain.value_objects.vault_status import VaultStatus


class InMemoryVaultRepository(VaultRepository):
    def __init__(self) -> None:
        now = datetime.now(timezone.utc)
        self._vaults: dict[str, Vault] = {
            "demo-vault-1": Vault(id="demo-vault-1", status=VaultStatus.LOCKED, last_seen_at=now),
            "demo-vault-2": Vault(id="demo-vault-2", status=VaultStatus.UNLOCKED, last_seen_at=now),
        }

    def get_by_id(self, vault_id: str) -> Vault | None:
        return self._vaults.get(vault_id)
