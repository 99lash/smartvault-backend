from dataclasses import dataclass
from datetime import datetime
from app.domain.value_objects.vault_status import VaultStatus


@dataclass(frozen=True)
class Vault:
    id: str
    owner_id: str
    hardware_uuid: str
    vault_name: str | None
    status: VaultStatus
    last_seen_at: datetime | None = None
    pin_hash: str | None = None
    pin_set_at: datetime | None = None
     
    @staticmethod
    def provisioned(
        *,
        id: str,
        owner_id: str,
        hardware_uuid: str,
        vault_name: str | None,
    ) -> "Vault":
        return Vault(
            id=id,
            owner_id=owner_id,
            hardware_uuid=hardware_uuid,
            vault_name=vault_name,
            status=VaultStatus.LOCKED,
            last_seen_at=None,
            pin_hash=None,
            pin_set_at=None,
        )
