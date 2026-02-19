"""Domain-level exceptions for vault authorization."""


class VaultAuthorizationError(Exception):
    """Base exception for vault authorization errors."""
    pass


class UnauthorizedVaultAccessError(VaultAuthorizationError):
    """Raised when user tries to access a vault they don't have permission for."""
    def __init__(self, user_id: str, vault_id: str):
        super().__init__("Unauthorized vault access")
        self.user_id = user_id
        self.vault_id = vault_id


class InsufficientPermissionsError(VaultAuthorizationError):
    """Raised when user's role doesn't have sufficient permissions."""
    def __init__(self, user_id: str, vault_id: str, role: str, required_action: str):
        super().__init__("Insufficient permissions for requested action")
        self.user_id = user_id
        self.vault_id = vault_id
        self.role = role
        self.required_action = required_action


class CannotRemoveOwnerError(VaultAuthorizationError):
    """Raised when attempting to remove the vault owner."""
    def __init__(self, vault_id: str):
        super().__init__("Cannot remove vault owner")
        self.vault_id = vault_id


class UserNotFoundError(Exception):
    """Raised when target user doesn't exist."""
    def __init__(self, user_id: str):
        super().__init__("User not found")
        self.user_id = user_id


class VaultNotFoundError(Exception):
    """Raised when vault doesn't exist."""
    def __init__(self, vault_id: str):
        super().__init__("Vault not found")
        self.vault_id = vault_id


class PINError(Exception):
    """Base exception for PIN-related errors."""
    pass


class PINNotSetError(PINError):
    """Raised when a PIN has not been configured for the vault."""
    def __init__(self, vault_id: str):
        super().__init__("PIN is not set for vault")
        self.vault_id = vault_id


class InvalidPINError(PINError):
    """Raised when a PIN value violates business rules or does not match."""
    def __init__(self, message: str = "Invalid PIN"):
        super().__init__(message)
        self.message = message


class PINLockedOutError(PINError):
    """Raised when PIN attempts are locked out due to too many failures."""
    def __init__(self, vault_id: str, attempts_remaining: int | None = None):
        if attempts_remaining is not None:
            super().__init__(f"PIN entry locked due to too many failed attempts; attempts remaining: {attempts_remaining}")
        else:
            super().__init__("PIN entry locked due to too many failed attempts")
        self.vault_id = vault_id
        self.attempts_remaining = attempts_remaining
