"""Tests to verify domain exceptions don't leak PII in string representations."""
from app.domain.exceptions import (
    UnauthorizedVaultAccessError,
    InsufficientPermissionsError,
    CannotRemoveOwnerError,
    UserNotFoundError,
    VaultNotFoundError,
    PINNotSetError,
    PINLockedOutError,
)


def test_unauthorized_vault_access_no_pii_in_str():
    """Verify UnauthorizedVaultAccessError doesn't expose user_id or vault_id in __str__."""
    exc = UnauthorizedVaultAccessError(user_id="user-123", vault_id="vault-456")
    
    error_str = str(exc)
    assert "user-123" not in error_str
    assert "vault-456" not in error_str
    assert "Unauthorized vault access" in error_str
    
    # Identifiers should still be accessible via properties
    assert exc.user_id == "user-123"
    assert exc.vault_id == "vault-456"


def test_insufficient_permissions_no_pii_in_str():
    """Verify InsufficientPermissionsError doesn't expose identifiers in __str__."""
    exc = InsufficientPermissionsError(
        user_id="user-789",
        vault_id="vault-012",
        role="VIEWER",
        required_action="delete_vault"
    )
    
    error_str = str(exc)
    assert "user-789" not in error_str
    assert "vault-012" not in error_str
    assert "Insufficient permissions" in error_str
    
    # Identifiers should still be accessible
    assert exc.user_id == "user-789"
    assert exc.vault_id == "vault-012"
    assert exc.role == "VIEWER"
    assert exc.required_action == "delete_vault"


def test_cannot_remove_owner_no_pii_in_str():
    """Verify CannotRemoveOwnerError doesn't expose vault_id in __str__."""
    exc = CannotRemoveOwnerError(vault_id="vault-345")
    
    error_str = str(exc)
    assert "vault-345" not in error_str
    assert "Cannot remove vault owner" in error_str
    
    assert exc.vault_id == "vault-345"


def test_user_not_found_no_pii_in_str():
    """Verify UserNotFoundError doesn't expose user_id in __str__."""
    exc = UserNotFoundError(user_id="user-678")
    
    error_str = str(exc)
    assert "user-678" not in error_str
    assert "User not found" in error_str
    
    assert exc.user_id == "user-678"


def test_vault_not_found_no_pii_in_str():
    """Verify VaultNotFoundError doesn't expose vault_id in __str__."""
    exc = VaultNotFoundError(vault_id="vault-901")
    
    error_str = str(exc)
    assert "vault-901" not in error_str
    assert "Vault not found" in error_str
    
    assert exc.vault_id == "vault-901"


def test_pin_not_set_no_pii_in_str():
    """Verify PINNotSetError doesn't expose vault_id in __str__."""
    exc = PINNotSetError(vault_id="vault-234")
    
    error_str = str(exc)
    assert "vault-234" not in error_str
    assert "PIN is not set" in error_str
    
    assert exc.vault_id == "vault-234"


def test_pin_locked_out_no_pii_in_str():
    """Verify PINLockedOutError doesn't expose vault_id in __str__."""
    exc = PINLockedOutError(vault_id="vault-567", attempts_remaining=0)
    
    error_str = str(exc)
    assert "vault-567" not in error_str
    assert "PIN entry locked" in error_str
    
    assert exc.vault_id == "vault-567"
    assert exc.attempts_remaining == 0


def test_pin_locked_out_no_attempts_remaining():
    """Verify PINLockedOutError without attempts_remaining parameter."""
    exc = PINLockedOutError(vault_id="vault-890")
    
    error_str = str(exc)
    assert "vault-890" not in error_str
    assert "PIN entry locked" in error_str
    
    assert exc.vault_id == "vault-890"
    assert exc.attempts_remaining is None
