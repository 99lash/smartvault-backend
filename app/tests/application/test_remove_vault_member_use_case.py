from datetime import datetime, timezone

import pytest

from app.application.use_cases.remove_vault_member import RemoveVaultMember, RemoveVaultMemberInput
from app.domain.exceptions import CannotRemoveOwnerError, UnauthorizedVaultAccessError, VaultNotFoundError
from app.domain.models.vault_authorization import VaultAuthorization
from app.domain.value_objects.vault_role import VaultRole
from app.infrastructure.db.repositories.in_memory_vault_authorization_repository import (
    InMemoryVaultAuthorizationRepository,
)
from app.infrastructure.db.repositories.in_memory_vault_repository import InMemoryVaultRepository


def _make_use_case():
    vault_repo = InMemoryVaultRepository()
    auth_repo = InMemoryVaultAuthorizationRepository()
    uc = RemoveVaultMember(vault_repo, auth_repo)
    return uc, vault_repo, auth_repo


def _seed_member(auth_repo: InMemoryVaultAuthorizationRepository, user_id: str):
    auth_repo.create(
        VaultAuthorization(
            id="auth-1",
            vault_id="demo-vault-1",
            user_id=user_id,
            role=VaultRole.MEMBER,
            granted_by="demo-user-1",
            granted_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
    )


def test_remove_member_success():
    uc, _, auth_repo = _make_use_case()
    _seed_member(auth_repo, "member-1")

    uc.execute(
        RemoveVaultMemberInput(
            vault_id="demo-vault-1",
            actor_user_id="demo-user-1",
            target_user_id="member-1",
        )
    )

    assert auth_repo.get_by_vault_and_user("demo-vault-1", "member-1") is None


def test_remove_member_idempotent():
    uc, _, auth_repo = _make_use_case()

    # No member seeded; should not raise
    uc.execute(
        RemoveVaultMemberInput(
            vault_id="demo-vault-1",
            actor_user_id="demo-user-1",
            target_user_id="absent-user",
        )
    )

    assert auth_repo.get_by_vault_and_user("demo-vault-1", "absent-user") is None


def test_remove_member_unauthorized_actor():
    uc, _, _ = _make_use_case()

    with pytest.raises(UnauthorizedVaultAccessError):
        uc.execute(
            RemoveVaultMemberInput(
                vault_id="demo-vault-1",
                actor_user_id="not-owner",
                target_user_id="member-1",
            )
        )


def test_remove_member_vault_not_found():
    uc, _, _ = _make_use_case()

    with pytest.raises(VaultNotFoundError):
        uc.execute(
            RemoveVaultMemberInput(
                vault_id="missing",
                actor_user_id="demo-user-1",
                target_user_id="member-1",
            )
        )


def test_remove_member_cannot_remove_owner():
    uc, vault_repo, _ = _make_use_case()
    owner_id = vault_repo.get_by_id("demo-vault-1").owner_id  # type: ignore[union-attr]

    with pytest.raises(CannotRemoveOwnerError):
        uc.execute(
            RemoveVaultMemberInput(
                vault_id="demo-vault-1",
                actor_user_id=owner_id,
                target_user_id=owner_id,
            )
        )
