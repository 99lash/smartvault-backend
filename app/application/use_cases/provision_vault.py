from dataclasses import dataclass
from uuid import uuid4

from app.application.ports.vault_repository import VaultRepository
from app.domain.models.vault import Vault
from app.domain.value_objects.vault_status import VaultStatus


class HardwareAlreadyProvisioned(Exception):
    pass


@dataclass(frozen=True)
class ProvisionVaultResult:
    vault: Vault


class ProvisionVault:
    def __init__(self, repo: VaultRepository) -> None:
        self._repo = repo

    def execute(
        self,
        *,
        owner_id: str,
        hardware_uuid: str,
        vault_name: str | None,
    ) -> ProvisionVaultResult:
        if self._repo.get_by_hardware_uuid(hardware_uuid) is not None:
            raise HardwareAlreadyProvisioned

        vault = Vault.provisioned(
            id=f"vault_{uuid4()}",
            owner_id=owner_id,
            hardware_uuid=hardware_uuid,
            vault_name=vault_name,
        )

        created = self._repo.create(vault)
        return ProvisionVaultResult(vault=created)

