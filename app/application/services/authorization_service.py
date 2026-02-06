from __future__ import annotations
from app.domain.value_objects.vault_role import VaultRole


class AuthorizationService:
    """
    Service for checking vault permissions.
    This is a stateless helper service.
    """

    @staticmethod
    def can_unlock(role: VaultRole | None, is_owner: bool) -> bool:
        """Check if a user with this role can unlock the vault."""
        if is_owner:
            return True
        if role is None:
            return False
        return role.can_unlock()

    @staticmethod
    def can_manage_members(role: VaultRole | None, is_owner: bool) -> bool:
        """Check if a user can add/remove members."""
        if is_owner:
            return True
        if role is None:
            return False
        return role.can_manage_members()

    @staticmethod
    def can_view_status(role: VaultRole | None, is_owner: bool) -> bool:
        """Check if a user can view vault status."""
        # Anyone with access can view status
        return is_owner or role is not None
