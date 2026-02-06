from __future__ import annotations
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class VaultRoleEnum(str, Enum):
    """API schema for VaultRole (mirrors domain enum)."""
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    VIEWER = "VIEWER"


class AddMemberRequest(BaseModel):
    """Request to add a member to a vault."""
    user_id: str = Field(..., description="ID of user to add as member")
    role: VaultRoleEnum = Field(..., description="Role to assign")


class MemberResponse(BaseModel):
    """Response with member details."""
    user_id: str
    email: str
    full_name: str | None
    role: VaultRoleEnum
    granted_at: datetime
    granted_by: str

    model_config = ConfigDict(from_attributes=True)


class MemberListResponse(BaseModel):
    """Response with list of vault members."""
    vault_id: str
    members: list[MemberResponse]
