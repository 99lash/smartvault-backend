from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    full_name: str | None = Field(default=None, max_length=200)


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class UpdateMeRequest(BaseModel):
    full_name: str | None = Field(default=None, max_length=200)


class UserSearchResult(BaseModel):
    user_id: str
    email: str
    full_name: str | None

    model_config = ConfigDict(from_attributes=True)


class RegisterDeviceTokenRequest(BaseModel):
    token: str = Field(min_length=10, max_length=512)
    platform: str = Field(pattern=r"^(ios|android)$")


class RegisterDeviceTokenResponse(BaseModel):
    registered: bool