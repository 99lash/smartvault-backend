from __future__ import annotations

from dataclasses import dataclass

from app.application.ports.vault_authorization_repository import VaultAuthorizationRepository
from app.application.use_cases.check_vault_access import CheckVaultAccess
from app.domain.exceptions import UnauthorizedVaultAccessError
from app.domain.models.vault_authorization import VaultAuthorization


@dataclass(frozen=True)
class ListVaultMembersResult:
    members: list[VaultAuthorization]


class ListVaultMembers:
    """List all authorizations for a vault (requires any access)."""

    def __init__(self, auth_repo: VaultAuthorizationRepository, check_access: CheckVaultAccess):
        self._auth_repo = auth_repo
        self._check_access = check_access

    def execute(self, vault_id: str, user_id: str) -> ListVaultMembersResult:
        access_info = self._check_access.execute(vault_id, user_id)
        if not access_info.has_access:
            raise UnauthorizedVaultAccessError(user_id, vault_id)

        members = self._auth_repo.list_by_vault(vault_id)
        return ListVaultMembersResult(members=members)
