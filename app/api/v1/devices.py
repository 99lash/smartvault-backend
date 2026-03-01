"""
Device-facing endpoints - called by firmware, no JWT auth.

POST /devices/register   - firmware registers after captive portal
POST /devices/verify-pin - firmware verifies keypad PIN entry
POST /devices/tamper     - firmware reports tamper detection
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from starlette.concurrency import run_in_threadpool

from app.api.deps.activity import get_log_activity_uc
from app.api.deps.vaults import get_register_device_uc, get_unlock_with_pin_uc, get_vault_repo
from app.application.ports.vault_repository import VaultRepository
from app.application.use_cases.log_activity import LogActivity, LogActivityInput
from app.application.use_cases.register_device import (
    HardwareAlreadyRegisteredError,
    InvalidProvisioningTokenError,
    RegisterDevice,
    RegisterDeviceInput,
)
from app.application.use_cases.unlock_vault_with_pin import UnlockVaultWithPIN, UnlockVaultWithPINInput
from app.domain.exceptions import InvalidPINError, PINLockedOutError, PINNotSetError
from app.domain.models.access_log import ActivityAction, ActivityMethod
from app.schemas.vaults import (
    RegisterDeviceRequest,
    RegisterDeviceResponse,
    TamperAlertRequest,
    TamperAlertResponse,
    VerifyPINRequest,
    VerifyPINResponse,
)

router = APIRouter(prefix="/devices", tags=["devices"])


@router.post(
    "/register",
    response_model=RegisterDeviceResponse,
    status_code=status.HTTP_200_OK,
)
async def register_device(
    payload: RegisterDeviceRequest,
    uc: RegisterDevice = Depends(get_register_device_uc),
) -> RegisterDeviceResponse:
    try:
        result = await run_in_threadpool(
            uc.execute,
            RegisterDeviceInput(
                hardware_uuid=payload.hardware_uuid,
                provisioning_token=payload.provisioning_token,
            ),
        )
        return RegisterDeviceResponse(vault_id=result.vault_id, vault_name=result.vault_name)
    except InvalidProvisioningTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired provisioning token")
    except HardwareAlreadyRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Hardware already registered - reset the vault first",
        )


@router.post(
    "/verify-pin",
    response_model=VerifyPINResponse,
    status_code=status.HTTP_200_OK,
)
async def verify_pin(
    payload: VerifyPINRequest,
    vault_repo: VaultRepository = Depends(get_vault_repo),
    uc: UnlockVaultWithPIN = Depends(get_unlock_with_pin_uc),
) -> VerifyPINResponse:
    vault = await run_in_threadpool(vault_repo.get_by_hardware_uuid, payload.hardware_uuid)
    if vault is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not registered")

    try:
        await uc.execute(
            UnlockVaultWithPINInput(
                vault_id=vault.id,
                pin=payload.pin,
                user_id=vault.owner_id,
            )
        )
        return VerifyPINResponse(unlocked=True)
    except PINNotSetError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="PIN not set")
    except PINLockedOutError as e:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=str(e))
    except InvalidPINError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid PIN")


@router.post(
    "/tamper",
    response_model=TamperAlertResponse,
    status_code=status.HTTP_200_OK,
)
async def tamper_alert(
    payload: TamperAlertRequest,
    vault_repo: VaultRepository = Depends(get_vault_repo),
    log_activity: LogActivity = Depends(get_log_activity_uc),
) -> TamperAlertResponse:
    vault = await run_in_threadpool(vault_repo.get_by_hardware_uuid, payload.hardware_uuid)
    if vault is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not registered")

    await run_in_threadpool(
        log_activity.execute,
        LogActivityInput(
            vault_id=vault.id,
            action=ActivityAction.TAMPER_DETECTED,
            method=ActivityMethod.SYSTEM,
            user_id=None,
            metadata={"hardware_uuid": payload.hardware_uuid},
        ),
    )
    return TamperAlertResponse(received=True)
