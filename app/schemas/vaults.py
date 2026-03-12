from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field
from app.domain.value_objects.vault_status import VaultStatus


class VaultStatusResponse(BaseModel):
    vault_id: str
    status: VaultStatus
    last_seen_at: datetime | None


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
    is_online: bool = False

    model_config = ConfigDict(populate_by_name=True)


class ProvisioningTokenResponse(BaseModel):
    provisioning_token: str


class ResetVaultResponse(BaseModel):
    reset: bool


class RegisterDeviceRequest(BaseModel):
    hardware_uuid: str
    provisioning_token: str


class RegisterDeviceResponse(BaseModel):
    vault_id: str
    vault_name: str | None = None


class VerifyPINRequest(BaseModel):
    hardware_uuid: str
    pin: str


class VerifyPINResponse(BaseModel):
    unlocked: bool


class TamperAlertRequest(BaseModel):
    hardware_uuid: str


class TamperAlertResponse(BaseModel):
    received: bool


class DeprovisionDeviceRequest(BaseModel):
    hardware_uuid: str


class DeprovisionDeviceResponse(BaseModel):
    deprovisioned: bool
    vault_id: str
