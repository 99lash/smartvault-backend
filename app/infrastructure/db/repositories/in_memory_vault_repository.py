from datetime import datetime, timezone
from app.application.services.vault_repository import VaultRepository
from app.domain.models.vault import Vault
from app.domain.value_objects.vault_status import VaultStatus


class InMemoryVaultRepository(VaultRepository):
    def __init__(self) -> None:
        now = datetime.now(timezone.utc)
        self._vaults: dict[str, Vault] = {
            "demo-vault-1": Vault(
                id="demo-vault-1",
                owner_id="demo-user-1",
                hardware_uuid="HW-DEMO-001",
                nickname="Demo Vault 1",
                status=VaultStatus.LOCKED,
                last_seen_at=now,
            ),
            "demo-vault-2": Vault(
                id="demo-vault-2",
                owner_id="demo-user-1",
                hardware_uuid="HW-DEMO-002",
                nickname="Demo Vault 2",
                status=VaultStatus.UNLOCKED,
                last_seen_at=now,
            ),
        }

    def get_by_id(self, vault_id: str) -> Vault | None:
        return self._vaults.get(vault_id)

    def get_by_hardware_uuid(self, hardware_uuid: str) -> Vault | None:
        for vault in self._vaults.values():
            if vault.hardware_uuid == hardware_uuid:
                return vault
        return None

    def create(self, vault: Vault) -> Vault:
        self._vaults[vault.id] = vault
        return vault
