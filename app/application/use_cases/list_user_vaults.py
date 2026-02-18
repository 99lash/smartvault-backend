from __future__ import annotations

from dataclasses import dataclass

from app.application.ports.vault_repository import VaultRepository
from app.domain.models.vault_access_summary import VaultAccessSummary


@dataclass(frozen=True)
class ListUserVaultsResult:
    vaults: list[VaultAccessSummary]


class ListUserVaults:
    """List all vaults a user owns or has access to."""

    def __init__(self, vault_repo: VaultRepository) -> None:
        self._vault_repo = vault_repo

    def execute(self, user_id: str) -> ListUserVaultsResult:
        vaults = self._vault_repo.list_for_user(user_id)
        return ListUserVaultsResult(vaults=vaults)
