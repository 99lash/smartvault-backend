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
from app.domain.exceptions import (
    UnauthorizedVaultAccessError,
    VaultNotFoundError,
)
from app.domain.models.vault_authorization import VaultAuthorization
from app.domain.value_objects.vault_role import VaultRole


@dataclass(frozen=True)
class AddVaultMemberInput:
    """
    Input for adding a member to a vault.

    Attributes:
        vault_id: The vault to add the member to.
        actor_user_id: The user performing the action (must be owner).
        target_user_id: The user to add as member.
        role: Role to assign to the new member.
        granted_at: Optional timestamp, defaults to now.
    """
    vault_id: str
    actor_user_id: str
    target_user_id: str
    role: VaultRole
    granted_at: datetime | None = None


@dataclass(frozen=True)
class AddVaultMemberResult:
    """
    Result of adding a vault member.

    Attributes:
        authorization: The created or updated VaultAuthorization record.
    """
    authorization: VaultAuthorization


class AddVaultMember:
    """
    Use case for vault owners to add or update vault members.

    Business Rules:
    - Only the vault owner can add members
    - Owner cannot be added as a member (already has implicit access)
    - Adding an existing member updates their role (idempotent)
    - Each vault can have only one authorization per user
    """

    def __init__(
        self,
        vault_repo: VaultRepository,
        auth_repo: VaultAuthorizationRepository
    ):
        """
        Initialize the use case with required repositories.

        Args:
            vault_repo: Repository to verify vault ownership.
            auth_repo: Repository to manage authorizations.
        """
        self._vault_repo = vault_repo
        self._auth_repo = auth_repo

    def execute(self, inp: AddVaultMemberInput) -> AddVaultMemberResult:
        """
        Add or update a vault member.

        This method handles both creating new authorizations and updating
        existing ones (idempotent operation).

        Args:
            inp: Input containing vault, actor, target user, and role.

        Returns:
            AddVaultMemberResult with the authorization record.

        Raises:
            VaultNotFoundError: If the vault doesn't exist.
            UnauthorizedVaultAccessError: If actor is not the owner.
            ValueError: If trying to add owner as a member.
        """
        # Step 1: Verify vault exists
        vault = self._vault_repo.get_by_id(inp.vault_id)
        if vault is None:
            raise VaultNotFoundError(inp.vault_id)

        # Step 2: Verify actor is the owner (only owners can add members)
        if vault.owner_id != inp.actor_user_id:
            raise UnauthorizedVaultAccessError(inp.actor_user_id, inp.vault_id)

        # Step 3: Prevent adding owner as a member (they already have access)
        # This is a business rule to maintain clear ownership semantics
        if inp.target_user_id == vault.owner_id:
            raise ValueError(
                "Owner already has implicit access and cannot be added as a member. "
                "Use the vault's owner_id for ownership operations."
            )

        # Step 4: Check for existing authorization (idempotent update)
        existing = self._auth_repo.get_by_vault_and_user(
            inp.vault_id,
            inp.target_user_id
        )

        # Use provided timestamp or current UTC time
        granted_at = inp.granted_at or datetime.now(timezone.utc)

        if existing:
            # Step 4a: Update existing member's role
            updated = self._auth_repo.update_role(
                inp.vault_id,
                inp.target_user_id,
                inp.role
            )
            return AddVaultMemberResult(authorization=updated or existing)

        # Step 4b: Create new authorization
        auth = VaultAuthorization(
            id=f"vaultauth_{uuid4()}",
            vault_id=inp.vault_id,
            user_id=inp.target_user_id,
            role=inp.role,
            granted_by=inp.actor_user_id,
            granted_at=granted_at,
        )
        created = self._auth_repo.create(auth)
        return AddVaultMemberResult(authorization=created)
