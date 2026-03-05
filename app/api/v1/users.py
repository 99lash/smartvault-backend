from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps.common import get_db_session
from app.api.deps.users import get_get_me_uc, get_update_me_uc, get_user_repo
from app.api.deps.auth import get_current_user_id
from app.application.ports.user_repository import UserRepository
from app.application.use_cases.get_me import GetMe
from app.application.use_cases.update_me import UpdateMe
from app.infrastructure.db.models.device_token_orm import DeviceTokenORM
from app.schemas.users import (
    CreateUserRequest,
    RegisterDeviceTokenRequest,
    RegisterDeviceTokenResponse,
    UpdateMeRequest,
    UserResponse,
    UserSearchResult,
)
from app.api.deps.users import get_create_user_uc
from app.application.use_cases.create_user import CreateUser, CreateUserInput, DuplicateEmailError

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: CreateUserRequest, uc: CreateUser = Depends(get_create_user_uc)) -> UserResponse:
    try:
        user = uc.execute(
            CreateUserInput(
                email=payload.email,
                password=payload.password,
                full_name=payload.full_name,
            )
        )
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            created_at=user.created_at,
        )
    except DuplicateEmailError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

@router.get("/me", response_model=UserResponse)
async def get_me(
    user_id: str = Depends(get_current_user_id),
    uc: GetMe = Depends(get_get_me_uc),
) -> UserResponse:
    user = uc.execute(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)

@router.patch("/me", response_model=UserResponse)
async def update_me(
    payload: UpdateMeRequest,
    user_id: str = Depends(get_current_user_id),
    uc: UpdateMe = Depends(get_update_me_uc),
) -> UserResponse:
    user = uc.execute(user_id, payload.full_name)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


@router.post("/me/device-token", response_model=RegisterDeviceTokenResponse)
async def register_device_token(
    payload: RegisterDeviceTokenRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_session),
) -> RegisterDeviceTokenResponse:
    """Register or update an Expo push token for the authenticated user."""
    existing = db.query(DeviceTokenORM).filter(DeviceTokenORM.token == payload.token).first()
    if existing:
        # Token already registered — reassign to current user (device re-login)
        existing.user_id = user_id  # type: ignore[assignment]
        db.commit()
    else:
        db.add(DeviceTokenORM(
            id=str(uuid.uuid4()),
            user_id=user_id,
            token=payload.token,
            platform=payload.platform,
        ))
        db.commit()
    return RegisterDeviceTokenResponse(registered=True)


@router.get("/search", response_model=UserSearchResult)
async def search_user_by_email(
    email: str,
    _: str = Depends(get_current_user_id),
    repo: UserRepository = Depends(get_user_repo),
) -> UserSearchResult:
    user = repo.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserSearchResult(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
    )