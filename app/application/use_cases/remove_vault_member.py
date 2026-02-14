from __future__ import annotations

from dataclasses import dataclass

from app.application.ports.vault_authorization_repository import VaultAuthorizationRepository
from app.application.ports.vault_repository import VaultRepository
from app.application.use_cases.log_activity import LogActivity, LogActivityInput
from app.domain.exceptions import (
    CannotRemoveOwnerError,
    UnauthorizedVaultAccessError,
    VaultNotFoundError,
)


@dataclass(frozen=True)
class RemoveVaultMemberInput:
    vault_id: str
    actor_user_id: str
    target_user_id: str


class RemoveVaultMember:
    """Use case for owners to remove a vault member."""

    def __init__(
        self,
        vault_repo: VaultRepository,
        auth_repo: VaultAuthorizationRepository,
        log_activity: LogActivity | None = None,  # NEW
    ):
        self._vault_repo = vault_repo
        self._auth_repo = auth_repo
        self._log_activity = log_activity

    def execute(self, inp: RemoveVaultMemberInput) -> None:
        vault = self._vault_repo.get_by_id(inp.vault_id)
        if vault is None:
            raise VaultNotFoundError(inp.vault_id)

        if vault.owner_id != inp.actor_user_id:
            raise UnauthorizedVaultAccessError(inp.actor_user_id, inp.vault_id)

        if inp.target_user_id == vault.owner_id:
            raise CannotRemoveOwnerError(inp.vault_id)

        self._auth_repo.delete(inp.vault_id, inp.target_user_id)

        if self._log_activity:
            try:
                self._log_activity.execute(LogActivityInput(
                    vault_id=inp.vault_id,
                    user_id=inp.actor_user_id,
                    action="MEMBER_REMOVED",
                    method="SYSTEM",
                    metadata={"target_user_id": inp.target_user_id},
                ))
            except Exception:
                pass