"""
Add Vault Member Use Case

Allows vault owners to add new members with specific roles.
Supports idempotent updates (changing an existing member's role).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.application.ports.vault_authorization_repository import VaultAuthorizationRepository
from app.application.ports.vault_repository import VaultRepository
from app.application.use_cases.log_activity import LogActivity, LogActivityInput
from app.domain.exceptions import (
    UnauthorizedVaultAccessError,
    VaultNotFoundError,
)
from app.domain.models.vault_authorization import VaultAuthorization
from app.domain.value_objects.vault_role import VaultRole
from app.infrastructure.monitoring.helpers import track_vault_member_added


@dataclass(frozen=True)
class AddVaultMemberInput:
    vault_id: str
    actor_user_id: str
    target_user_id: str
    role: VaultRole
    granted_at: datetime | None = None


@dataclass(frozen=True)
class AddVaultMemberResult:
    authorization: VaultAuthorization


class AddVaultMember:
    def __init__(
        self,
        vault_repo: VaultRepository,
        auth_repo: VaultAuthorizationRepository,
        log_activity: LogActivity | None = None,  # NEW
    ):
        self._vault_repo = vault_repo
        self._auth_repo = auth_repo
        self._log_activity = log_activity

    def execute(self, inp: AddVaultMemberInput) -> AddVaultMemberResult:
        if not inp.target_user_id:
            raise ValueError("Target user is required")

        vault = self._vault_repo.get_by_id(inp.vault_id)
        if vault is None:
            raise VaultNotFoundError(inp.vault_id)

        if vault.owner_id != inp.actor_user_id:
            raise UnauthorizedVaultAccessError(inp.actor_user_id, inp.vault_id)

        if inp.target_user_id == vault.owner_id:
            raise ValueError(
                "Owner already has implicit access and cannot be added as a member. "
                "Use the vault's owner_id for ownership operations."
            )

        existing = self._auth_repo.get_by_vault_and_user(
            inp.vault_id,
            inp.target_user_id,
        )

        granted_at = inp.granted_at or datetime.now(timezone.utc)

        if existing:
            updated = self._auth_repo.update_role(
                inp.vault_id,
                inp.target_user_id,
                inp.role,
            )
            if not updated:
                raise RuntimeError("Authorization missing during role update")

            track_vault_member_added(role=inp.role.value)

            if self._log_activity:
                try:
                    self._log_activity.execute(LogActivityInput(
                        vault_id=inp.vault_id,
                        user_id=inp.actor_user_id,
                        action="MEMBER_ADDED",
                        method="SYSTEM",
                        metadata={
                            "target_user_id": inp.target_user_id,
                            "role": inp.role.value,
                            "operation": "role_updated",
                        },
                    ))
                except Exception:
                    pass

            return AddVaultMemberResult(authorization=updated)

        auth = VaultAuthorization(
            id=f"vaultauth_{uuid4()}",
            vault_id=inp.vault_id,
            user_id=inp.target_user_id,
            role=inp.role,
            granted_by=inp.actor_user_id,
            granted_at=granted_at,
        )
        created = self._auth_repo.create(auth)

        track_vault_member_added(role=inp.role.value)

        if self._log_activity:
            try:
                self._log_activity.execute(LogActivityInput(
                    vault_id=inp.vault_id,
                    user_id=inp.actor_user_id,
                    action="MEMBER_ADDED",
                    method="SYSTEM",
                    metadata={
                        "target_user_id": inp.target_user_id,
                        "role": inp.role.value,
                        "operation": "added",
                    },
                ))
            except Exception:
                pass

        return AddVaultMemberResult(authorization=created)
