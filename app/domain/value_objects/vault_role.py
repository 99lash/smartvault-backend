from __future__ import annotations
from enum import Enum


class VaultRole(str, Enum):
    """
    Roles for vault access authorization.

    Role Hierarchy (highest to lowest):
    1. OWNER - implicit role from vault.owner_id (full access, not stored in DB)
    2. ADMIN - can unlock vault + manage members
    3. MEMBER - can unlock vault only
    4. VIEWER - view status only, cannot unlock
    """
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    VIEWER = "VIEWER"

    def can_unlock(self) -> bool:
        """
        Check if this role can unlock the vault.

        Returns:
            True for ADMIN and MEMBER roles (can unlock).
            False for VIEWER (read-only access).
        """
        return self in (VaultRole.ADMIN, VaultRole.MEMBER)

    def can_manage_members(self) -> bool:
        """
        Check if this role can add/remove vault members.

        Only ADMIN role has member management permissions.
        OWNER implicitly has this permission (checked separately).

        Returns:
            True only for ADMIN role.
        """
        return self == VaultRole.ADMIN

    @classmethod
    def can_view_status(cls, role: "VaultRole | None") -> bool:
        """
        Check if this role can view vault status.

        All roles except None can view status.
        This is the most permissive permission.

        Args:
            role: The user's vault role, or None if no access.

        Returns:
            True if user has any vault role.
        """
        return role is not None
