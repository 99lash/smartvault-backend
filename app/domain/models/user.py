from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class User:
    """
    Domain model (no framework/ORM types here).
    """
    id: str
    email: str
    password_hash: str
    full_name: str | None
    created_at: datetime
    provisioning_token: str | None = None
