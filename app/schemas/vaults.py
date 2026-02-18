from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field
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


class VaultAccessRoleEnum(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    VIEWER = "VIEWER"


class VaultListItemResponse(BaseModel):
    vault_id: str
    vault_name: str | None = Field(default=None, alias="name")
    status: VaultStatus
    role: VaultAccessRoleEnum
    last_seen_at: datetime | None

    model_config = ConfigDict(populate_by_name=True)
