from __future__ import annotations

from pydantic import BaseModel


class AdminPingResponse(BaseModel):
    """Response for admin connectivity check."""

    status: str
    admin_api: str
    version: str