from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

from app.domain.value_objects.vault_role import VaultRole


@dataclass(frozen=True)
class VaultAuthorization:
    """
    Domain model for vault member authorization.

    Note: Vault OWNER is implicit (vault.owner_id), not stored here.
    This model represents additional members with specific roles.
    """
    id: str
    vault_id: str
    user_id: str
    role: VaultRole
    granted_by: str | None  # user_id of who granted access
    granted_at: datetime
