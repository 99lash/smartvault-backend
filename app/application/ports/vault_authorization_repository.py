from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional

from app.domain.models.vault_authorization import VaultAuthorization
from app.domain.value_objects.vault_role import VaultRole


class VaultAuthorizationRepository(ABC):
    """Port for vault authorization persistence."""

    @abstractmethod
    def create(self, auth: VaultAuthorization) -> VaultAuthorization:
        """Create a new vault authorization."""
        raise NotImplementedError

    @abstractmethod
    def update_role(self, vault_id: str, user_id: str, role: VaultRole) -> VaultAuthorization | None:
        """Update an existing member's role. Returns None if not found."""
        raise NotImplementedError

    @abstractmethod
    def get_by_vault_and_user(self, vault_id: str, user_id: str) -> Optional[VaultAuthorization]:
        """Get authorization for a specific user on a vault."""
        raise NotImplementedError

    @abstractmethod
    def list_by_vault(self, vault_id: str) -> list[VaultAuthorization]:
        """List all authorizations for a vault."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, vault_id: str, user_id: str) -> None:
        """Remove a user's authorization from a vault."""
        raise NotImplementedError

    @abstractmethod
    def user_has_access(self, vault_id: str, user_id: str) -> bool:
        """Check if user has any authorization for a vault (quick check)."""
        raise NotImplementedError

    @abstractmethod
    def get_user_role(self, vault_id: str, user_id: str) -> VaultRole | None:
        """Get user's role for a vault, or None if no access."""
        raise NotImplementedError
