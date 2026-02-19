"""Tests to verify API logging doesn't expose PII."""
from datetime import datetime, timezone
from dataclasses import replace

from app.domain.models.user import User
from app.domain.models.vault_authorization import VaultAuthorization
from app.domain.value_objects.vault_role import VaultRole
from app.infrastructure.db.repositories.in_memory_vault_authorization_repository import (
    InMemoryVaultAuthorizationRepository,
)


def _seed_user(repo, user_id: str, email: str, full_name: str | None = None):
    user = User(
        id=user_id,
        email=email,
        password_hash="x",
        full_name=full_name,
        created_at=datetime.now(timezone.utc),
    )
    repo.create(user)
    return user


def _set_vault_owner(vault_repo, vault_id: str, owner_id: str):
    vault = vault_repo._vaults[vault_id]
    vault_repo._vaults[vault_id] = replace(vault, owner_id=owner_id)


def test_list_members_missing_users_no_raw_ids_in_logs(
    client, vault_repo, vault_auth_repo: InMemoryVaultAuthorizationRepository, user_repo, capsys
):
    """Verify that when users are missing, logs don't contain raw user IDs."""
    owner_id = "test-user-id"
    _set_vault_owner(vault_repo, "demo-vault-1", owner_id)
    _seed_user(user_repo, owner_id, "owner@example.com")
    
    # Create authorization for a user that doesn't exist in user_repo
    vault_auth_repo.create(
        VaultAuthorization(
            id="auth-1",
            vault_id="demo-vault-1",
            user_id="missing-user-999",
            role=VaultRole.MEMBER,
            granted_by=owner_id,
            granted_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
    )
    
    resp = client.get("/api/v1/vaults/demo-vault-1/members")
    
    assert resp.status_code == 404
    
    # Capture stdout/stderr where structlog outputs
    captured = capsys.readouterr()
    log_output = captured.out + captured.err
    
    # Should have logged the warning with count
    assert "resource_not_found" in log_output
    assert "missing_user_count=1" in log_output
    
    # Should NOT contain the raw user ID
    assert "missing-user-999" not in log_output


def test_add_member_exception_no_raw_ids_in_logs(client, vault_repo, user_repo, capsys):
    """Verify exceptions don't leak user/vault IDs in logs."""
    # Don't seed the owner - this will trigger UnauthorizedVaultAccessError
    _seed_user(user_repo, "test-user-id", "test@example.com")
    _seed_user(user_repo, "member-1", "member1@example.com")
    
    resp = client.post(
        "/api/v1/vaults/demo-vault-1/members",
        json={"user_id": "member-1", "role": "MEMBER"},
    )
    
    assert resp.status_code == 403
    
    # Capture stdout/stderr
    captured = capsys.readouterr()
    log_output = captured.out + captured.err
    
    # Verify logs don't contain raw IDs
    assert "demo-vault-1" not in log_output
    assert "member-1" not in log_output
    assert "test-user-id" not in log_output


def test_remove_member_exception_no_raw_ids_in_logs(client, vault_repo, user_repo, capsys):
    """Verify remove member exceptions don't leak IDs in logs."""
    # Don't seed the owner - this will trigger UnauthorizedVaultAccessError
    _seed_user(user_repo, "test-user-id", "test@example.com")
    
    resp = client.delete("/api/v1/vaults/demo-vault-1/members/some-member")
    
    assert resp.status_code == 403
    
    # Capture stdout/stderr
    captured = capsys.readouterr()
    log_output = captured.out + captured.err
    
    # Verify logs don't contain raw IDs
    assert "demo-vault-1" not in log_output
    assert "some-member" not in log_output
    assert "test-user-id" not in log_output
