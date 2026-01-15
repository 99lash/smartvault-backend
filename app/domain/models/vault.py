from dataclasses import dataclass
from datetime import datetime
from app.domain.value_objects.vault_status import VaultStatus


@dataclass(frozen=True)
class Vault:
    id: str
    owner_id: str
    hardware_uuid: str
    nickname: str | None
    status: VaultStatus
    last_seen_at: datetime | None = None
