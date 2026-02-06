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


def test_add_member_success(client, vault_repo, vault_auth_repo: InMemoryVaultAuthorizationRepository, user_repo):
    owner_id = "test-user-id"
    _set_vault_owner(vault_repo, "demo-vault-1", owner_id)
    _seed_user(user_repo, owner_id, "owner@example.com", "Owner")
    _seed_user(user_repo, "member-1", "member1@example.com", "Member One")

    resp = client.post(
        "/api/v1/vaults/demo-vault-1/members",
        json={"user_id": "member-1", "role": "MEMBER"},
    )

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["user_id"] == "member-1"
    assert data["role"] == "MEMBER"
    assert data["email"] == "member1@example.com"
    assert vault_auth_repo.get_by_vault_and_user("demo-vault-1", "member-1") is not None


def test_add_member_forbidden_when_not_owner(client, vault_repo, user_repo):
    _set_vault_owner(vault_repo, "demo-vault-1", "someone-else")
    _seed_user(user_repo, "test-user-id", "owner@example.com")
    _seed_user(user_repo, "member-1", "member1@example.com")

    resp = client.post(
        "/api/v1/vaults/demo-vault-1/members",
        json={"user_id": "member-1", "role": "MEMBER"},
    )

    assert resp.status_code == 403


def test_remove_member_success(client, vault_repo, vault_auth_repo: InMemoryVaultAuthorizationRepository, user_repo):
    owner_id = "test-user-id"
    _set_vault_owner(vault_repo, "demo-vault-1", owner_id)
    _seed_user(user_repo, owner_id, "owner@example.com")
    _seed_user(user_repo, "member-2", "member2@example.com")

    # Seed auth directly
    vault_auth_repo.create(
        VaultAuthorization(
            id="auth-1",
            vault_id="demo-vault-1",
            user_id="member-2",
            role=VaultRole.MEMBER,
            granted_by=owner_id,
            granted_at=datetime.now(timezone.utc),
        )
    )

    resp = client.delete("/api/v1/vaults/demo-vault-1/members/member-2")
    assert resp.status_code == 204, resp.text
    assert vault_auth_repo.get_by_vault_and_user("demo-vault-1", "member-2") is None


def test_list_members(client, vault_repo, vault_auth_repo: InMemoryVaultAuthorizationRepository, user_repo):
    owner_id = "test-user-id"
    _set_vault_owner(vault_repo, "demo-vault-1", owner_id)
    _seed_user(user_repo, owner_id, "owner@example.com")
    _seed_user(user_repo, "member-1", "member1@example.com")

    # Seed auth
    vault_auth_repo.create(
        VaultAuthorization(
            id="auth-1",
            vault_id="demo-vault-1",
            user_id="member-1",
            role=VaultRole.MEMBER,
            granted_by=owner_id,
            granted_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
    )

    resp = client.get("/api/v1/vaults/demo-vault-1/members")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["vault_id"] == "demo-vault-1"
    assert len(data["members"]) == 1
    assert data["members"][0]["user_id"] == "member-1"
