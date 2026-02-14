"""
Integration tests verifying activity logging is called
by use cases when LogActivity is injected.

These tests use the InMemoryActivityLogRepository directly
to confirm events are persisted after each operation.
"""

from __future__ import annotations

import pytest
from dataclasses import replace
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from app.application.use_cases.log_activity import LogActivity
from app.application.use_cases.unlock_vault_with_pin import (
    UnlockVaultWithPIN,
    UnlockVaultWithPINInput,
)
from app.application.use_cases.set_vault_pin import SetVaultPIN, SetVaultPINInput
from app.application.use_cases.remove_vault_pin import RemoveVaultPIN, RemoveVaultPINInput
from app.application.use_cases.add_vault_member import AddVaultMember, AddVaultMemberInput
from app.application.use_cases.remove_vault_member import (
    RemoveVaultMember,
    RemoveVaultMemberInput,
)
from app.domain.value_objects.pin_attempt_result import PINAttemptResult
from app.domain.value_objects.vault_role import VaultRole
from app.domain.value_objects.vault_status import VaultStatus
from app.domain.models.vault import Vault
from app.infrastructure.db.repositories.in_memory_vault_repository import InMemoryVaultRepository
from app.infrastructure.db.repositories.in_memory_activity_log_repository import (
    InMemoryActivityLogRepository,
)


# =============================================================================
# HELPERS
# =============================================================================

def _make_log_activity() -> tuple[LogActivity, InMemoryActivityLogRepository]:
    """Create a LogActivity use case backed by an in-memory repo."""
    repo = InMemoryActivityLogRepository()
    return LogActivity(repo), repo


def _make_vault(vault_id: str = "vault-1", owner_id: str = "user-1", pin_hash: str | None = "hash"):
    """Create a minimal vault."""
    return Vault(
        id=vault_id,
        owner_id=owner_id,
        hardware_uuid="hw-uuid-1",
        vault_name="Test Vault",
        status=VaultStatus.UNLOCKED,
        pin_hash=pin_hash,
    )


def _make_vault_repo(vault=None):
    """Create a vault repo with the given vault pre-loaded."""
    repo = InMemoryVaultRepository()
    # Seed the repo with the vault these tests expect to exist
    repo.create(vault or _make_vault())
    return repo


def _make_hasher(verify_result: bool = True):
    """Create a PIN hasher mock."""
    hasher = MagicMock()
    hasher.verify.return_value = verify_result
    hasher.hash.return_value = "new-hash"
    return hasher


def _make_tracker(locked_out: bool = False):
    """Create a PIN attempt tracker mock."""
    tracker = MagicMock()
    tracker.is_locked_out = AsyncMock(return_value=locked_out)
    tracker.register_success = AsyncMock()
    tracker.register_failure = AsyncMock(return_value=(PINAttemptResult.INVALID, 2))
    return tracker


# =============================================================================
# UNLOCK VAULT WITH PIN — LOGGING TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_unlock_success_logs_vault_unlocked():
    """Successful unlock records VAULT_UNLOCKED in activity log."""
    log_activity, repo = _make_log_activity()
    uc = UnlockVaultWithPIN(
        repo=_make_vault_repo(),
        hasher=_make_hasher(verify_result=True),
        tracker=_make_tracker(),
        log_activity=log_activity,
    )

    await uc.execute(UnlockVaultWithPINInput(
        vault_id="vault-1",
        pin="827364",
        user_id="user-1",
    ))

    logs = repo.list_by_vault("vault-1")
    assert len(logs) == 1
    assert logs[0].action == "VAULT_UNLOCKED"
    assert logs[0].user_id == "user-1"
    assert logs[0].method == "PIN"


@pytest.mark.asyncio
async def test_unlock_wrong_pin_logs_vault_unlock_failed():
    """Wrong PIN records VAULT_UNLOCK_FAILED in activity log."""
    log_activity, repo = _make_log_activity()
    uc = UnlockVaultWithPIN(
        repo=_make_vault_repo(),
        hasher=_make_hasher(verify_result=False),
        tracker=_make_tracker(),
        log_activity=log_activity,
    )

    with pytest.raises(Exception):
        await uc.execute(UnlockVaultWithPINInput(
            vault_id="vault-1",
            pin="918273",
            user_id="user-1",
        ))

    logs = repo.list_by_vault("vault-1")
    assert len(logs) == 1
    assert logs[0].action == "VAULT_UNLOCK_FAILED"
    assert logs[0].metadata["reason"] == "wrong_pin"


@pytest.mark.asyncio
async def test_unlock_locked_out_logs_vault_unlock_failed():
    """Locked-out vault records VAULT_UNLOCK_FAILED with lockout=True."""
    log_activity, repo = _make_log_activity()
    uc = UnlockVaultWithPIN(
        repo=_make_vault_repo(),
        hasher=_make_hasher(),
        tracker=_make_tracker(locked_out=True),
        log_activity=log_activity,
    )

    with pytest.raises(Exception):
        await uc.execute(UnlockVaultWithPINInput(
            vault_id="vault-1",
            pin="000000",
            user_id="user-1",
        ))

    logs = repo.list_by_vault("vault-1")
    assert len(logs) == 1
    assert logs[0].action == "VAULT_UNLOCK_FAILED"
    assert logs[0].metadata["lockout"] is True


@pytest.mark.asyncio
async def test_unlock_without_log_activity_does_not_raise():
    """UnlockVaultWithPIN works normally when log_activity is None."""
    uc = UnlockVaultWithPIN(
        repo=_make_vault_repo(),
        hasher=_make_hasher(verify_result=True),
        tracker=_make_tracker(),
        log_activity=None,
    )

    result = await uc.execute(UnlockVaultWithPINInput(
        vault_id="vault-1",
        pin="827364",
    ))

    assert result.result == PINAttemptResult.SUCCESS


# =============================================================================
# SET VAULT PIN — LOGGING TESTS
# =============================================================================

def test_set_pin_logs_pin_set():
    """Setting a PIN records PIN_SET in activity log."""
    log_activity, repo = _make_log_activity()
    uc = SetVaultPIN(
        repo=_make_vault_repo(),
        hasher=_make_hasher(),
        log_activity=log_activity,
    )

    uc.execute(SetVaultPINInput(vault_id="vault-1", pin="827364", user_id="user-1"))

    logs = repo.list_by_vault("vault-1")
    assert len(logs) == 1
    assert logs[0].action == "PIN_SET"
    assert logs[0].user_id == "user-1"


def test_set_pin_without_log_activity_does_not_raise():
    """SetVaultPIN works normally when log_activity is None."""
    uc = SetVaultPIN(
        repo=_make_vault_repo(),
        hasher=_make_hasher(),
        log_activity=None,
    )

    result = uc.execute(SetVaultPINInput(vault_id="vault-1", pin="827364"))
    assert result.vault is not None


# =============================================================================
# REMOVE VAULT PIN — LOGGING TESTS
# =============================================================================

def test_remove_pin_logs_pin_set_with_removed_metadata():
    """Removing a PIN records PIN_SET with operation=removed in activity log."""
    log_activity, repo = _make_log_activity()
    vault = _make_vault(pin_hash="existing-hash")
    uc = RemoveVaultPIN(
        repo=_make_vault_repo(vault),
        log_activity=log_activity,
    )

    uc.execute(RemoveVaultPINInput(vault_id="vault-1", user_id="user-1"))

    logs = repo.list_by_vault("vault-1")
    assert len(logs) == 1
    assert logs[0].action == "PIN_SET"
    assert logs[0].metadata["operation"] == "removed"


# =============================================================================
# ADD VAULT MEMBER — LOGGING TESTS
# =============================================================================

def test_add_member_logs_member_added():
    """Adding a member records MEMBER_ADDED in activity log."""
    log_activity, repo = _make_log_activity()

    vault = _make_vault(owner_id="owner-1")
    vault_repo = _make_vault_repo(vault)

    auth_repo = MagicMock()
    auth_repo.get_by_vault_and_user.return_value = None
    auth_repo.create.return_value = MagicMock(
        id="auth-1",
        vault_id="vault-1",
        user_id="member-1",
        role=VaultRole.MEMBER,
        granted_by="owner-1",
        granted_at=datetime.now(timezone.utc),
    )

    uc = AddVaultMember(
        vault_repo=vault_repo,
        auth_repo=auth_repo,
        log_activity=log_activity,
    )

    uc.execute(AddVaultMemberInput(
        vault_id="vault-1",
        actor_user_id="owner-1",
        target_user_id="member-1",
        role=VaultRole.MEMBER,
    ))

    logs = repo.list_by_vault("vault-1")
    assert len(logs) == 1
    assert logs[0].action == "MEMBER_ADDED"
    assert logs[0].metadata["target_user_id"] == "member-1"


# =============================================================================
# REMOVE VAULT MEMBER — LOGGING TESTS
# =============================================================================

def test_remove_member_logs_member_removed():
    """Removing a member records MEMBER_REMOVED in activity log."""
    log_activity, repo = _make_log_activity()

    vault = _make_vault(owner_id="owner-1")
    vault_repo = _make_vault_repo(vault)

    auth_repo = MagicMock()
    auth_repo.delete.return_value = None

    uc = RemoveVaultMember(
        vault_repo=vault_repo,
        auth_repo=auth_repo,
        log_activity=log_activity,
    )

    uc.execute(RemoveVaultMemberInput(
        vault_id="vault-1",
        actor_user_id="owner-1",
        target_user_id="member-1",
    ))

    logs = repo.list_by_vault("vault-1")
    assert len(logs) == 1
    assert logs[0].action == "MEMBER_REMOVED"
    assert logs[0].metadata["target_user_id"] == "member-1"
