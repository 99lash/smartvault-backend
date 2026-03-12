"""
Device-facing endpoints - called by firmware, no JWT auth.

POST /devices/register    - firmware registers after captive portal
POST /devices/verify-pin  - firmware verifies keypad PIN entry
POST /devices/tamper      - firmware reports tamper detection
POST /devices/deprovision - firmware deletes vault on reprovision
"""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.api.deps.activity import get_log_activity_uc
from app.api.deps.common import get_db_session
from app.api.deps.vaults import (
    get_delete_vault_uc,
    get_register_device_uc,
    get_unlock_with_pin_uc,
    get_vault_repo,
)
from app.infrastructure.notifications.push_service import push_service
from app.application.ports.vault_repository import VaultRepository
from app.application.use_cases.log_activity import LogActivity, LogActivityInput
from app.application.use_cases.delete_vault import DeleteVault, DeleteVaultInput
from app.application.use_cases.register_device import (
    HardwareAlreadyRegisteredError,
    InvalidProvisioningTokenError,
    RegisterDevice,
    RegisterDeviceInput,
)
from app.application.use_cases.unlock_vault_with_pin import UnlockVaultWithPIN, UnlockVaultWithPINInput
from app.domain.exceptions import (
    InvalidPINError,
    PINLockedOutError,
    PINNotSetError,
    UnauthorizedVaultAccessError,
    VaultNotFoundError,
)
from app.schemas.vaults import (
    DeprovisionDeviceRequest,
    DeprovisionDeviceResponse,
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
        result = await uc.execute(
            RegisterDeviceInput(
                hardware_uuid=payload.hardware_uuid,
                provisioning_token=payload.provisioning_token,
            )
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
    db: Session = Depends(get_db_session),
) -> TamperAlertResponse:
    vault = await run_in_threadpool(vault_repo.get_by_hardware_uuid, payload.hardware_uuid)
    if vault is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not registered")

    await run_in_threadpool(
        log_activity.execute,
        LogActivityInput(
            vault_id=vault.id,
            action="TAMPER_DETECTED",
            method="SYSTEM",
            user_id=None,
            metadata={"hardware_uuid": payload.hardware_uuid},
        ),
    )

    asyncio.create_task(
        push_service.send_to_user(
            db,
            vault.owner_id,
            title="Tamper Alert",
            body="Tamper detected on your vault. Check immediately.",
            data={"vault_id": str(vault.id), "event": "TAMPER_DETECTED"},
        )
    )

    return TamperAlertResponse(received=True)


@router.post(
    "/deprovision",
    response_model=DeprovisionDeviceResponse,
    status_code=status.HTTP_200_OK,
)
async def deprovision_device(
    payload: DeprovisionDeviceRequest,
    vault_repo: VaultRepository = Depends(get_vault_repo),
    uc: DeleteVault = Depends(get_delete_vault_uc),
) -> DeprovisionDeviceResponse:
    vault = await run_in_threadpool(vault_repo.get_by_hardware_uuid, payload.hardware_uuid)
    if vault is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not registered")

    try:
        await run_in_threadpool(
            uc.execute,
            DeleteVaultInput(vault_id=vault.id, requesting_user_id=vault.owner_id),
        )
        return DeprovisionDeviceResponse(deprovisioned=True, vault_id=vault.id)
    except VaultNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vault not found")
    except UnauthorizedVaultAccessError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to deprovision")
