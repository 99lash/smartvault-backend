from dataclasses import dataclass
from uuid import uuid4

from app.application.ports.vault_repository import VaultRepository, VaultAlreadyExistsError
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
        existing = self._repo.get_by_hardware_uuid(hardware_uuid)
        if existing is not None:
            if existing.status != VaultStatus.PROVISIONING:
                raise HardwareAlreadyProvisioned
            # Re-provision in-place: vault was reset, same device re-registering
            reprovisioned = Vault(
                id=existing.id,
                owner_id=owner_id,
                hardware_uuid=hardware_uuid,
                vault_name=vault_name or existing.vault_name,
                status=VaultStatus.LOCKED,
                last_seen_at=None,
                pin_hash=None,
                pin_set_at=None,
            )
            updated = self._repo.update(reprovisioned)
            return ProvisionVaultResult(vault=updated)

        vault = Vault.provisioned(
            id=f"vault_{uuid4()}",
            owner_id=owner_id,
            hardware_uuid=hardware_uuid,
            vault_name=vault_name,
        )

        try:
            created = self._repo.create(vault)
        except VaultAlreadyExistsError:
            raise HardwareAlreadyProvisioned

        return ProvisionVaultResult(vault=created)

