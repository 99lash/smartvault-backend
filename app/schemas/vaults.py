from datetime import datetime
from pydantic import BaseModel
from app.domain.value_objects.vault_status import VaultStatus


class VaultStatusResponse(BaseModel):
    vault_id: str
    status: VaultStatus
    last_seen_at: datetime | None


class ProvisionVaultRequest(BaseModel):
    hardware_uuid: str
    vault_name: str | None = None


class ProvisionVaultResponse(BaseModel):
    vault_id: str
    hardware_uuid: str
    vault_name: str | None
    status: VaultStatus


class UnlockCommandResponse(BaseModel):
    command_id: str
    vault_id: str
    expires_at: datetime
    sent: bool
