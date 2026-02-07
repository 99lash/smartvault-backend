from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.value_objects.pin_attempt_result import PINAttemptResult


class SetPINRequest(BaseModel):
    pin: str = Field(..., min_length=6, max_length=6, description="6-digit numeric PIN")


class SetPINResponse(BaseModel):
    vault_id: str
    pin_set_at: datetime


class RemovePINResponse(BaseModel):
    vault_id: str
    removed: bool = True


class PINStatusResponse(BaseModel):
    vault_id: str
    is_set: bool
    pin_set_at: datetime | None


class UnlockWithPINRequest(BaseModel):
    pin: str = Field(..., min_length=6, max_length=6, description="6-digit numeric PIN")


class UnlockWithPINResponse(BaseModel):
    vault_id: str
    result: PINAttemptResult
    attempts_remaining: int | None = None
