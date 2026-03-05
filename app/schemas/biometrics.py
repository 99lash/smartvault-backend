from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.vaults import VaultListItemResponse


class BiometricEnrollResponse(BaseModel):
    enrolled: bool
    enrolled_at: datetime


class BiometricVerifyRequest(BaseModel):
    user_id: str
    vault_id: str | None = None   # If provided, send unlock signal to this vault


class BiometricVerifyResponse(BaseModel):
    success: bool
    vaults: list[VaultListItemResponse]
    unlock_sent: bool | None = None      # True if unlock command was dispatched
    vault_offline: bool | None = None    # True if vault was offline at verify time


class FaceEnrollResponse(BaseModel):
    enrolled: bool


class FaceVerifyResponse(BaseModel):
    success: bool
    unlock_sent: bool | None = None
    vault_offline: bool | None = None
