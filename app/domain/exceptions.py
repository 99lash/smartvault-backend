"""Domain-level exceptions for vault authorization."""


class VaultAuthorizationError(Exception):
    """Base exception for vault authorization errors."""
    pass


class UnauthorizedVaultAccessError(VaultAuthorizationError):
    """Raised when user tries to access a vault they don't have permission for."""
    def __init__(self, user_id: str, vault_id: str):
        super().__init__(f"User {user_id} does not have access to vault {vault_id}")
        self.user_id = user_id
        self.vault_id = vault_id


class InsufficientPermissionsError(VaultAuthorizationError):
    """Raised when user's role doesn't have sufficient permissions."""
    def __init__(self, user_id: str, vault_id: str, role: str, required_action: str):
        super().__init__(
            f"User {user_id} with role {role} cannot perform '{required_action}' on vault {vault_id}"
        )
        self.user_id = user_id
        self.vault_id = vault_id
        self.role = role
        self.required_action = required_action


class CannotRemoveOwnerError(VaultAuthorizationError):
    """Raised when attempting to remove the vault owner."""
    def __init__(self, vault_id: str):
        super().__init__(f"Cannot remove owner from vault {vault_id}")
        self.vault_id = vault_id


class UserNotFoundError(Exception):
    """Raised when target user doesn't exist."""
    def __init__(self, user_id: str):
        super().__init__(f"User {user_id} not found")
        self.user_id = user_id


class VaultNotFoundError(Exception):
    """Raised when vault doesn't exist."""
    def __init__(self, vault_id: str):
        super().__init__(f"Vault {vault_id} not found")
        self.vault_id = vault_id
