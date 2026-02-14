from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.application.use_cases.log_activity import LogActivity, LogActivityInput
from app.infrastructure.db.repositories.in_memory_activity_log_repository import (
    InMemoryActivityLogRepository,
)


@pytest.fixture
def repo():
    r = InMemoryActivityLogRepository()
    yield r
    r.clear()


@pytest.fixture
def use_case(repo):
    return LogActivity(repo)


# =============================================================================
# execute()
# =============================================================================

def test_execute_returns_access_log(use_case):
    """execute() returns the persisted AccessLog."""
    result = use_case.execute(LogActivityInput(
        vault_id="vault-1",
        action="VAULT_UNLOCKED",
        method="PIN",
        user_id="user-1",
    ))

    assert result.vault_id == "vault-1"
    assert result.action == "VAULT_UNLOCKED"
    assert result.method == "PIN"
    assert result.user_id == "user-1"


def test_execute_generates_unique_ids(use_case):
    """Each call produces a unique log ID."""
    inp = LogActivityInput(vault_id="v1", action="PIN_SET", method="PIN")
    r1 = use_case.execute(inp)
    r2 = use_case.execute(inp)
    assert r1.id != r2.id


def test_execute_sets_created_at(use_case):
    """created_at is set to a recent UTC timestamp."""
    before = datetime.now(timezone.utc)
    result = use_case.execute(LogActivityInput(
        vault_id="v1", action="PIN_SET", method="PIN",
    ))
    after = datetime.now(timezone.utc)

    assert before <= result.created_at <= after


def test_execute_persists_to_repo(use_case, repo):
    """Log entry is retrievable from the repository after execute()."""
    use_case.execute(LogActivityInput(
        vault_id="vault-persist",
        action="MEMBER_ADDED",
        method="SYSTEM",
    ))

    entries = repo.list_by_vault("vault-persist")
    assert len(entries) == 1
    assert entries[0].action == "MEMBER_ADDED"


def test_execute_stores_metadata(use_case, repo):
    """Metadata dict is preserved in the stored entry."""
    meta = {"role": "MEMBER", "granted_by": "user-owner"}
    use_case.execute(LogActivityInput(
        vault_id="v1",
        action="MEMBER_ADDED",
        method="SYSTEM",
        metadata=meta,
    ))

    entries = repo.list_by_vault("v1")
    assert entries[0].metadata == meta


def test_execute_allows_null_user_id(use_case, repo):
    """System events with no user_id are accepted."""
    use_case.execute(LogActivityInput(
        vault_id="v1",
        action="VAULT_STATE_CHANGED",
        method="SYSTEM",
        user_id=None,
    ))

    entries = repo.list_by_vault("v1")
    assert entries[0].user_id is None


def test_execute_multiple_actions(use_case, repo):
    """Multiple events for same vault are all stored."""
    for action in ("VAULT_UNLOCKED", "VAULT_UNLOCK_FAILED", "PIN_SET"):
        use_case.execute(LogActivityInput(
            vault_id="v1", action=action, method="PIN",  # type: ignore[arg-type]
        ))

    entries = repo.list_by_vault("v1")
    assert len(entries) == 3