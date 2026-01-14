from datetime import datetime
from pydantic import BaseModel
from app.domain.value_objects.vault_status import VaultStatus


class VaultStatusResponse(BaseModel):
    vault_id: str
    status: VaultStatus
    last_seen_at: datetime | None
