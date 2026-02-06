from datetime import datetime, timezone

import pytest

from app.application.use_cases.add_vault_member import AddVaultMember, AddVaultMemberInput
from app.domain.exceptions import UnauthorizedVaultAccessError, VaultNotFoundError
from app.domain.value_objects.vault_role import VaultRole
from app.infrastructure.db.repositories.in_memory_vault_authorization_repository import (
    InMemoryVaultAuthorizationRepository,
)
from app.infrastructure.db.repositories.in_memory_vault_repository import InMemoryVaultRepository


def _make_use_case():
    vault_repo = InMemoryVaultRepository()
    auth_repo = InMemoryVaultAuthorizationRepository()
    uc = AddVaultMember(vault_repo, auth_repo)
    return uc, vault_repo, auth_repo


def test_add_member_success():
    uc, _, auth_repo = _make_use_case()

    result = uc.execute(
        AddVaultMemberInput(
            vault_id="demo-vault-1",
            actor_user_id="demo-user-1",
            target_user_id="member-1",
            role=VaultRole.MEMBER,
            granted_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
    )

    auth = result.authorization
    assert auth.vault_id == "demo-vault-1"
    assert auth.user_id == "member-1"
    assert auth.role == VaultRole.MEMBER
    assert auth.granted_by == "demo-user-1"
    assert auth_repo.get_by_vault_and_user("demo-vault-1", "member-1") is not None


def test_add_member_updates_existing_role():
    uc, _, auth_repo = _make_use_case()

    # initial add
    uc.execute(
        AddVaultMemberInput(
            vault_id="demo-vault-1",
            actor_user_id="demo-user-1",
            target_user_id="member-1",
            role=VaultRole.MEMBER,
        )
    )

    # update role
    result = uc.execute(
        AddVaultMemberInput(
            vault_id="demo-vault-1",
            actor_user_id="demo-user-1",
            target_user_id="member-1",
            role=VaultRole.ADMIN,
        )
    )

    auth = result.authorization
    assert auth.role == VaultRole.ADMIN
    assert auth_repo.get_by_vault_and_user("demo-vault-1", "member-1").role == VaultRole.ADMIN


def test_add_member_unauthorized_actor():
    uc, _, _ = _make_use_case()

    with pytest.raises(UnauthorizedVaultAccessError):
        uc.execute(
            AddVaultMemberInput(
                vault_id="demo-vault-1",
                actor_user_id="not-owner",
                target_user_id="member-1",
                role=VaultRole.VIEWER,
            )
        )


def test_add_member_vault_not_found():
    uc, _, _ = _make_use_case()

    with pytest.raises(VaultNotFoundError):
        uc.execute(
            AddVaultMemberInput(
                vault_id="missing-vault",
                actor_user_id="demo-user-1",
                target_user_id="member-1",
                role=VaultRole.MEMBER,
            )
        )


def test_add_member_cannot_add_owner():
    uc, vault_repo, _ = _make_use_case()
    owner_id = vault_repo.get_by_id("demo-vault-1").owner_id  # type: ignore[union-attr]

    with pytest.raises(ValueError):
        uc.execute(
            AddVaultMemberInput(
                vault_id="demo-vault-1",
                actor_user_id=owner_id,
                target_user_id=owner_id,
                role=VaultRole.MEMBER,
            )
        )
