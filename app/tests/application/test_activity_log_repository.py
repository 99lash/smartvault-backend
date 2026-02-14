from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.domain.models.access_log import AccessLog
from app.infrastructure.db.repositories.in_memory_activity_log_repository import (
    InMemoryActivityLogRepository,
)


# =============================================================================
# HELPERS
# =============================================================================

def _make_log(
    *,
    vault_id: str = "vault-1",
    user_id: str | None = "user-1",
    action: str = "VAULT_UNLOCKED",
    method: str = "PIN",
    metadata: dict | None = None,
    created_at: datetime | None = None,
) -> AccessLog:
    return AccessLog(
        id=f"log-{uuid4()}",
        vault_id=vault_id,
        user_id=user_id,
        action=action,          # type: ignore[arg-type]
        method=method,          # type: ignore[arg-type]
        metadata=metadata,
        created_at=created_at or datetime.now(timezone.utc),
    )


@pytest.fixture
def repo() -> InMemoryActivityLogRepository:
    r = InMemoryActivityLogRepository()
    yield r
    r.clear()


# =============================================================================
# create()
# =============================================================================

def test_create_returns_the_log(repo):
    """create() returns the same AccessLog that was passed in."""
    log = _make_log()
    result = repo.create(log)
    assert result == log


def test_create_persists_log(repo):
    """After create(), the log appears in list_by_vault()."""
    log = _make_log(vault_id="vault-abc")
    repo.create(log)

    results = repo.list_by_vault("vault-abc")
    assert len(results) == 1
    assert results[0].id == log.id


def test_create_stores_metadata(repo):
    """Metadata dict is preserved exactly."""
    meta = {"previous_status": "LOCKED", "new_status": "UNLOCKED"}
    log = _make_log(metadata=meta)
    repo.create(log)

    results = repo.list_by_vault(log.vault_id)
    assert results[0].metadata == meta


def test_create_allows_null_user_id(repo):
    """System-triggered events with no user_id are accepted."""
    log = _make_log(user_id=None, action="VAULT_STATE_CHANGED", method="SYSTEM")
    repo.create(log)

    results = repo.list_by_vault(log.vault_id)
    assert results[0].user_id is None


# =============================================================================
# list_by_vault()
# =============================================================================

def test_list_by_vault_filters_by_vault(repo):
    """list_by_vault() returns only logs for the requested vault."""
    repo.create(_make_log(vault_id="vault-A"))
    repo.create(_make_log(vault_id="vault-A"))
    repo.create(_make_log(vault_id="vault-B"))

    results = repo.list_by_vault("vault-A")
    assert len(results) == 2
    assert all(r.vault_id == "vault-A" for r in results)


def test_list_by_vault_orders_newest_first(repo):
    """Entries are returned newest-first."""
    now = datetime.now(timezone.utc)
    old = _make_log(vault_id="v1", created_at=now - timedelta(hours=2))
    mid = _make_log(vault_id="v1", created_at=now - timedelta(hours=1))
    new = _make_log(vault_id="v1", created_at=now)

    repo.create(old)
    repo.create(new)
    repo.create(mid)

    results = repo.list_by_vault("v1")
    assert results[0].id == new.id
    assert results[1].id == mid.id
    assert results[2].id == old.id


def test_list_by_vault_respects_limit(repo):
    """limit parameter caps the number of results."""
    for _ in range(10):
        repo.create(_make_log(vault_id="vault-1"))

    results = repo.list_by_vault("vault-1", limit=3)
    assert len(results) == 3


def test_list_by_vault_hard_caps_at_100(repo):
    """Requests for more than 100 entries are silently capped at 100."""
    for _ in range(120):
        repo.create(_make_log(vault_id="vault-1"))

    results = repo.list_by_vault("vault-1", limit=200)
    assert len(results) == 100


def test_list_by_vault_before_cursor(repo):
    """before= cursor excludes entries at or after the given timestamp."""
    now = datetime.now(timezone.utc)
    old = _make_log(vault_id="v1", created_at=now - timedelta(hours=3))
    mid = _make_log(vault_id="v1", created_at=now - timedelta(hours=2))
    new = _make_log(vault_id="v1", created_at=now - timedelta(hours=1))

    for log in (old, mid, new):
        repo.create(log)

    # Ask for entries before `mid` — should only return `old`
    results = repo.list_by_vault("v1", before=mid.created_at)
    assert len(results) == 1
    assert results[0].id == old.id


def test_list_by_vault_returns_empty_for_unknown_vault(repo):
    """Unknown vault_id returns empty list, not an error."""
    results = repo.list_by_vault("does-not-exist")
    assert results == []


# =============================================================================
# count_recent_by_action()
# =============================================================================

def test_count_recent_by_action_counts_correctly(repo):
    """Counts matching action entries since the given timestamp."""
    now = datetime.now(timezone.utc)
    repo.create(_make_log(action="VAULT_UNLOCK_FAILED", created_at=now - timedelta(minutes=5)))
    repo.create(_make_log(action="VAULT_UNLOCK_FAILED", created_at=now - timedelta(minutes=3)))
    repo.create(_make_log(action="VAULT_UNLOCK_FAILED", created_at=now - timedelta(minutes=1)))
    repo.create(_make_log(action="VAULT_UNLOCKED", created_at=now - timedelta(minutes=2)))

    count = repo.count_recent_by_action(
        "VAULT_UNLOCK_FAILED",
        since=now - timedelta(minutes=10),
    )
    assert count == 3


def test_count_recent_by_action_excludes_old_entries(repo):
    """Entries older than `since` are not counted."""
    now = datetime.now(timezone.utc)
    repo.create(_make_log(action="VAULT_UNLOCK_FAILED", created_at=now - timedelta(hours=2)))
    repo.create(_make_log(action="VAULT_UNLOCK_FAILED", created_at=now - timedelta(minutes=5)))

    # Window is last 1 hour — should only count the recent one
    count = repo.count_recent_by_action(
        "VAULT_UNLOCK_FAILED",
        since=now - timedelta(hours=1),
    )
    assert count == 1


def test_count_recent_by_action_returns_zero_when_none(repo):
    """Returns 0 when no matching entries exist."""
    count = repo.count_recent_by_action(
        "VAULT_UNLOCK_FAILED",
        since=datetime.now(timezone.utc),
    )
    assert count == 0


def test_count_recent_by_action_ignores_other_actions(repo):
    """Other action types don't pollute the count."""
    now = datetime.now(timezone.utc)
    repo.create(_make_log(action="VAULT_UNLOCKED", created_at=now))
    repo.create(_make_log(action="PIN_SET", created_at=now))

    count = repo.count_recent_by_action(
        "VAULT_UNLOCK_FAILED",
        since=now - timedelta(minutes=10),
    )
    assert count == 0