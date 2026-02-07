from datetime import datetime, timezone

import pytest

from app.application.use_cases.check_vault_access import CheckVaultAccess
from app.domain.exceptions import VaultNotFoundError
from app.domain.models.vault_authorization import VaultAuthorization
from app.domain.value_objects.vault_role import VaultRole
from app.infrastructure.db.repositories.in_memory_vault_authorization_repository import (
    InMemoryVaultAuthorizationRepository,
)
from app.infrastructure.db.repositories.in_memory_vault_repository import InMemoryVaultRepository


def _make_use_case():
    vault_repo = InMemoryVaultRepository()
    auth_repo = InMemoryVaultAuthorizationRepository()
    uc = CheckVaultAccess(vault_repo, auth_repo)
    return uc, vault_repo, auth_repo


def test_check_access_owner():
    uc, _, _ = _make_use_case()

    info = uc.execute("demo-vault-1", "demo-user-1")

    assert info.has_access is True
    assert info.is_owner is True
    assert info.role is None


def test_check_access_member():
    uc, _, auth_repo = _make_use_case()
    auth_repo.create(
        VaultAuthorization(
            id="auth-1",
            vault_id="demo-vault-1",
            user_id="member-1",
            role=VaultRole.ADMIN,
            granted_by="demo-user-1",
            granted_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
    )

    info = uc.execute("demo-vault-1", "member-1")

    assert info.has_access is True
    assert info.is_owner is False
    assert info.role == VaultRole.ADMIN


def test_check_access_denied():
    uc, _, _ = _make_use_case()

    info = uc.execute("demo-vault-1", "stranger")

    assert info.has_access is False
    assert info.is_owner is False
    assert info.role is None


def test_check_access_vault_not_found():
    uc, _, _ = _make_use_case()

    with pytest.raises(VaultNotFoundError):
        uc.execute("missing-vault", "someone")
