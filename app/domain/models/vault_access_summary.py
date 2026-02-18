from __future__ import annotations

from dataclasses import dataclass

from app.domain.models.vault import Vault
from app.domain.value_objects.vault_role import VaultRole


@dataclass(frozen=True)
class VaultAccessSummary:
    vault: Vault
    role: VaultRole | None
    is_owner: bool
