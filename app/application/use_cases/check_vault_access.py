"""
Check Vault Access Use Case

Provides centralized access policy enforcement for vault operations.
This is a foundational use case used by other use cases to verify permissions.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.ports.vault_authorization_repository import VaultAuthorizationRepository
from app.application.ports.vault_repository import VaultRepository
from app.domain.exceptions import VaultNotFoundError
from app.domain.value_objects.vault_role import VaultRole


@dataclass(frozen=True)
class VaultAccessInfo:
    """
    Result of an access check operation.

    Attributes:
        has_access: True if user has any access to the vault.
        role: User's role (None for OWNER, as ownership is implicit).
        is_owner: True if user is the vault owner.
    """
    has_access: bool
    role: VaultRole | None
    is_owner: bool


class CheckVaultAccess:
    """
    Centralized access policy for vault operations.

    This use case determines if a user has access to a vault and returns
    their role information. It serves as the single source of truth for
    access decisions across the application.

    Access Resolution Order:
    1. Check if vault exists (raises VaultNotFoundError if not)
    2. Check if user is the owner (implicit full access)
    3. Check vault_authorizations table for role-based access
    """

    def __init__(
        self,
        vault_repo: VaultRepository,
        auth_repo: VaultAuthorizationRepository
    ) -> None:
        """
        Initialize the access checker with required repositories.

        Args:
            vault_repo: Repository to fetch vault data (for owner check).
            auth_repo: Repository to fetch authorization records.
        """
        self._vault_repo = vault_repo
        self._auth_repo = auth_repo

    def execute(self, vault_id: str, user_id: str) -> VaultAccessInfo:
        """
        Check if a user has access to a vault.

        This method implements the access resolution logic:
        - Owner always has full access (role=None indicates ownership)
        - Members have access based on their stored role
        - Non-members have no access

        Args:
            vault_id: The vault to check access for.
            user_id: The user requesting access.

        Returns:
            VaultAccessInfo with access details.

        Raises:
            VaultNotFoundError: If the vault does not exist.
        """
        # Step 1: Verify vault exists and get ownership info
        vault = self._vault_repo.get_by_id(vault_id)
        if vault is None:
            raise VaultNotFoundError(vault_id)

        # Step 2: Owner has implicit full access (not stored in authorizations)
        if vault.owner_id == user_id:
            return VaultAccessInfo(
                has_access=True,
                role=None,  # None indicates OWNER
                is_owner=True
            )

        # Step 3: Check role-based access from vault_authorizations table
        role = self._auth_repo.get_user_role(vault_id, user_id)
        if role is None:
            # User exists but has no vault authorization
            return VaultAccessInfo(
                has_access=False,
                role=None,
                is_owner=False
            )

        # Step 4: User has role-based access
        return VaultAccessInfo(
            has_access=True,
            role=role,
            is_owner=False
        )
