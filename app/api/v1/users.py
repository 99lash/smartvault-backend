from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_create_user_uc
from app.application.use_cases.create_user import CreateUser, CreateUserInput, DuplicateEmailError
from app.schemas.users import CreateUserRequest, UserResponse

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
