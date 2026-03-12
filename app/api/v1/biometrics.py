from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.api.deps.auth import get_current_user_id
from app.api.deps.common import get_db_session
from app.api.deps.vaults import (
    get_check_vault_access_uc,
    get_list_user_vaults_uc,
    get_send_unlock_command_uc,
    get_vault_repo,
    get_ws_manager,
)
from app.application.use_cases.delete_face import DeleteFace, DeleteFaceInput
from app.application.use_cases.enroll_biometrics import EnrollBiometrics, EnrollBiometricsInput
from app.application.use_cases.enroll_face import EnrollFace, EnrollFaceInput
from app.application.use_cases.list_user_vaults import ListUserVaults
from app.application.use_cases.send_unlock_command import SendUnlockCommand, VaultOfflineError
from app.application.use_cases.verify_face import (
    FaceNotEnrolledError,
    FaceVerificationFailedError,
    VerifyFace,
    VerifyFaceInput,
)
from app.domain.exceptions import InsufficientPermissionsError, UnauthorizedVaultAccessError
from app.domain.value_objects.vault_role import VaultRole
from app.domain.value_objects.websocket_messages import MessageType
from app.infrastructure.db.models.biometric_enrollment_orm import BiometricEnrollmentORM
from app.infrastructure.db.models.face_encoding_orm import FaceEncodingORM
from app.infrastructure.messaging.websocket_manager import WebSocketManager
from app.infrastructure.notifications.push_service import push_service
from app.schemas.biometrics import (
    BiometricEnrollResponse,
    BiometricVerifyRequest,
    BiometricVerifyResponse,
    FaceDeleteResponse,
    FaceEnrollResponse,
    FaceStatusResponse,
    FaceVerifyResponse,
)
from app.schemas.vaults import VaultAccessRoleEnum, VaultListItemResponse

_MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB

router = APIRouter(prefix="/biometrics", tags=["biometrics"])


def _get_enroll_uc(db: Session = Depends(get_db_session)) -> EnrollBiometrics:
    return EnrollBiometrics(db)


def _vault_to_response(summary) -> VaultListItemResponse:
    role_map = {
        VaultRole.ADMIN: VaultAccessRoleEnum.ADMIN,
        VaultRole.MEMBER: VaultAccessRoleEnum.MEMBER,
        VaultRole.VIEWER: VaultAccessRoleEnum.VIEWER,
    }
    role = role_map.get(summary.role, VaultAccessRoleEnum.OWNER) if summary.role else VaultAccessRoleEnum.OWNER
    return VaultListItemResponse(
        vault_id=summary.vault.id,
        name=summary.vault.vault_name,
        status=summary.vault.status,
        role=role,
        last_seen_at=summary.vault.last_seen_at,
    )


@router.post("/enroll", response_model=BiometricEnrollResponse)
async def enroll_biometric(
    user_id: str = Depends(get_current_user_id),
    uc: EnrollBiometrics = Depends(_get_enroll_uc),
) -> BiometricEnrollResponse:
    """Record biometric enrollment for the authenticated user."""
    result = await run_in_threadpool(
        uc.execute,
        EnrollBiometricsInput(user_id=user_id),
    )
    return BiometricEnrollResponse(enrolled=result.enrolled, enrolled_at=result.enrolled_at)


@router.post("/verify", response_model=BiometricVerifyResponse)
async def verify_biometric(
    payload: BiometricVerifyRequest,
    jwt_user_id: str = Depends(get_current_user_id),
    list_vaults_uc: ListUserVaults = Depends(get_list_user_vaults_uc),
    unlock_uc: SendUnlockCommand = Depends(get_send_unlock_command_uc),
    ws_manager: WebSocketManager = Depends(get_ws_manager),
    db: Session = Depends(get_db_session),
) -> BiometricVerifyResponse:
    """
    Validate biometric session:
    1. JWT user must match claimed user_id
    2. Returns user's vaults
    3. If vault_id provided: verify ownership → send unlock signal → notify user
    """
    # Step 1: JWT ↔ body user_id must match
    if payload.user_id != jwt_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="user_id does not match authenticated token",
        )

    # Step 2: Fetch user's vaults
    result = await run_in_threadpool(list_vaults_uc.execute, jwt_user_id)
    vaults = [_vault_to_response(s) for s in result.vaults]

    # Step 3: Update last_used_at for audit
    enrollment = (
        db.query(BiometricEnrollmentORM)
        .filter(BiometricEnrollmentORM.user_id == jwt_user_id)
        .first()
    )
    if enrollment:
        enrollment.last_used_at = datetime.now(timezone.utc)  # type: ignore[assignment]
        db.commit()

    # Step 4: If vault_id provided, verify ownership + send unlock signal
    unlock_sent: bool | None = None
    vault_offline: bool | None = None

    if payload.vault_id:
        vault_id = payload.vault_id
        try:
            await unlock_uc.execute(vault_id=vault_id, user_id=jwt_user_id)
            unlock_sent = True
            vault_offline = False

            # Notify the user via WebSocket (in-app) and push (background)
            await ws_manager.send_to_user(
                jwt_user_id,
                {
                    "type": MessageType.NOTIFICATION.value,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "payload": {
                        "title": "Vault Unlocked",
                        "message": f"Vault {vault_id} was unlocked via biometric authentication.",
                        "severity": "success",
                        "vault_id": vault_id,
                    },
                },
            )
            asyncio.create_task(
                push_service.send_to_user(
                    db, jwt_user_id,
                    title="Vault Unlocked 🔓",
                    body="Your vault was unlocked via biometric authentication.",
                    data={"vault_id": vault_id, "event": "VAULT_UNLOCKED"},
                )
            )

        except VaultOfflineError:
            unlock_sent = False
            vault_offline = True
            # Notify user — vault was offline (WebSocket + push)
            await ws_manager.send_to_user(
                jwt_user_id,
                {
                    "type": MessageType.NOTIFICATION.value,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "payload": {
                        "title": "Vault Offline",
                        "message": f"Vault {vault_id} is offline. Unlock signal could not be sent.",
                        "severity": "warning",
                        "vault_id": vault_id,
                    },
                },
            )
            asyncio.create_task(
                push_service.send_to_user(
                    db, jwt_user_id,
                    title="Vault Offline ⚠️",
                    body="Your vault is offline. Unlock signal could not be sent.",
                    data={"vault_id": vault_id, "event": "VAULT_OFFLINE"},
                )
            )

        except UnauthorizedVaultAccessError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this vault",
            )

        except InsufficientPermissionsError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your role does not permit unlocking this vault",
            )

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )

    return BiometricVerifyResponse(
        success=True,
        vaults=vaults,
        unlock_sent=unlock_sent,
        vault_offline=vault_offline,
    )


@router.post("/enroll-face", response_model=FaceEnrollResponse, status_code=status.HTTP_200_OK)
async def enroll_face(
    image: UploadFile = File(..., description="JPEG or PNG photo of the user's face"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_session),
) -> FaceEnrollResponse:
    """Encode and store the authenticated user's face for server-side recognition."""
    image_bytes = await image.read()
    if len(image_bytes) > _MAX_IMAGE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Image too large (max 5 MB)")

    uc = EnrollFace(db)
    try:
        result = await run_in_threadpool(uc.execute, EnrollFaceInput(user_id=user_id, image_bytes=image_bytes))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return FaceEnrollResponse(enrolled=result.enrolled)


@router.get("/face/status", response_model=FaceStatusResponse, status_code=status.HTTP_200_OK)
async def face_status(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_session),
) -> FaceStatusResponse:
    """Return whether the authenticated user currently has a stored face encoding."""
    face_record = (
        db.query(FaceEncodingORM)
        .filter(FaceEncodingORM.user_id == user_id)
        .first()
    )

    return FaceStatusResponse(
        enrolled=face_record is not None,
        updated_at=face_record.updated_at if face_record else None,
    )


@router.post("/verify-face", response_model=FaceVerifyResponse)
async def verify_face(
    image: UploadFile = File(..., description="JPEG or PNG photo to verify against stored encoding"),
    vault_id: str | None = Form(None, description="If provided, send an unlock command to this vault on match"),
    user_id: str = Depends(get_current_user_id),
    unlock_uc: SendUnlockCommand = Depends(get_send_unlock_command_uc),
    db: Session = Depends(get_db_session),
) -> FaceVerifyResponse:
    """Verify face against stored encoding. On match, optionally unlock a vault."""
    image_bytes = await image.read()
    if len(image_bytes) > _MAX_IMAGE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Image too large (max 5 MB)")

    uc = VerifyFace(db)
    try:
        await run_in_threadpool(uc.execute, VerifyFaceInput(user_id=user_id, image_bytes=image_bytes))
    except FaceNotEnrolledError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Face not enrolled. Please enroll first.")
    except FaceVerificationFailedError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Face verification failed.")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Face matched — optionally send unlock command
    unlock_sent: bool | None = None
    vault_offline: bool | None = None

    if vault_id:
        try:
            await unlock_uc.execute(vault_id=vault_id, user_id=user_id)
            unlock_sent = True
            vault_offline = False
        except VaultOfflineError:
            unlock_sent = False
            vault_offline = True
        except UnauthorizedVaultAccessError:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this vault")
        except InsufficientPermissionsError:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your role does not permit unlocking this vault")
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return FaceVerifyResponse(success=True, unlock_sent=unlock_sent, vault_offline=vault_offline)


@router.delete("/face", response_model=FaceDeleteResponse)
async def delete_face(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_session),
) -> FaceDeleteResponse:
    """Delete the authenticated user's stored face encoding."""
    uc = DeleteFace(db)
    result = await run_in_threadpool(uc.execute, DeleteFaceInput(user_id=user_id))
    return FaceDeleteResponse(deleted=result.deleted)
