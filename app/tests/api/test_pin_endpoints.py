from dataclasses import replace
from datetime import datetime, timezone

import pytest

from app.api import deps as deps_root
from app.api.deps import vaults as vault_deps
from app.application.ports.pin_attempt_tracker import PINAttemptTracker
from app.application.ports.pin_hasher import PINHasher
from app.domain.models.vault import Vault
from app.domain.value_objects.pin import PIN
from app.domain.value_objects.pin_attempt_result import PINAttemptResult


class _FakeHasher(PINHasher):
    def hash(self, pin: PIN) -> str:
        return f"hash:{pin.value}"

    def verify(self, pin: PIN, hashed_pin: str) -> bool:
        return hashed_pin == f"hash:{pin.value}"


class _FakeTracker(PINAttemptTracker):
    def __init__(self, max_attempts: int = 2) -> None:
        self.max_attempts = max_attempts
        self.counts: dict[str, int] = {}

    def _inc(self, vault_id: str) -> int:
        self.counts[vault_id] = self.counts.get(vault_id, 0) + 1
        return self.counts[vault_id]

    async def register_failure(self, vault_id: str):
        count = self._inc(vault_id)
        if count >= self.max_attempts:
            return PINAttemptResult.LOCKED_OUT, 0
        remaining = self.max_attempts - count
        return PINAttemptResult.INVALID, remaining

    async def register_success(self, vault_id: str):
        self.counts[vault_id] = 0

    async def is_locked_out(self, vault_id: str) -> bool:
        return self.counts.get(vault_id, 0) >= self.max_attempts


def _set_vault_owner(vault_repo, vault_id: str, owner_id: str):
    vault: Vault = vault_repo._vaults[vault_id]
    vault_repo._vaults[vault_id] = replace(vault, owner_id=owner_id)


@pytest.fixture
def pin_deps(app, vault_repo):
    hasher = _FakeHasher()
    tracker = _FakeTracker(max_attempts=2)

    app.dependency_overrides[vault_deps.get_pin_hasher] = lambda: hasher
    app.dependency_overrides[vault_deps.get_pin_attempt_tracker] = lambda: tracker

    yield hasher, tracker

    app.dependency_overrides.pop(vault_deps.get_pin_hasher, None)
    app.dependency_overrides.pop(vault_deps.get_pin_attempt_tracker, None)


def test_set_pin_success(client, vault_repo, pin_deps):
    hasher, _ = pin_deps
    _set_vault_owner(vault_repo, "demo-vault-1", "test-user-id")

    resp = client.post("/api/v1/vaults/demo-vault-1/pin", json={"pin": "827364"})

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["vault_id"] == "demo-vault-1"
    assert data["pin_set_at"] is not None
    assert vault_repo._vaults["demo-vault-1"].pin_hash == hasher.hash(PIN("827364"))


def test_set_pin_invalid_pattern(client, vault_repo, pin_deps):
    _set_vault_owner(vault_repo, "demo-vault-1", "test-user-id")

    resp = client.post("/api/v1/vaults/demo-vault-1/pin", json={"pin": "111111"})

    assert resp.status_code == 422


def test_remove_pin_success(client, vault_repo, pin_deps):
    hasher, _ = pin_deps
    _set_vault_owner(vault_repo, "demo-vault-1", "test-user-id")
    # Seed pin
    vault_repo.update_pin(
        "demo-vault-1",
        hasher.hash(PIN("827364")),
        datetime.now(timezone.utc),
    )

    resp = client.delete("/api/v1/vaults/demo-vault-1/pin")

    assert resp.status_code == 200, resp.text
    assert resp.json()["removed"] is True
    assert vault_repo._vaults["demo-vault-1"].pin_hash is None


def test_remove_pin_when_not_set(client, vault_repo, pin_deps):
    _set_vault_owner(vault_repo, "demo-vault-1", "test-user-id")

    resp = client.delete("/api/v1/vaults/demo-vault-1/pin")

    assert resp.status_code == 409


def test_get_pin_status(client, vault_repo, pin_deps):
    hasher, _ = pin_deps
    _set_vault_owner(vault_repo, "demo-vault-1", "test-user-id")
    vault_repo.update_pin(
        "demo-vault-1",
        hasher.hash(PIN("827364")),
        datetime(2026, 2, 7, tzinfo=timezone.utc),
    )

    resp = client.get("/api/v1/vaults/demo-vault-1/pin/status")

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["vault_id"] == "demo-vault-1"
    assert data["is_set"] is True
    assert data["pin_set_at"] is not None


def test_unlock_with_pin_success(client, vault_repo, pin_deps):
    hasher, tracker = pin_deps
    _set_vault_owner(vault_repo, "demo-vault-1", "test-user-id")
    vault_repo.update_pin(
        "demo-vault-1",
        hasher.hash(PIN("827364")),
        datetime.now(timezone.utc),
    )

    resp = client.post("/api/v1/vaults/demo-vault-1/unlock/pin", json={"pin": "827364"})

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["result"] == PINAttemptResult.SUCCESS.value
    assert tracker.counts.get("demo-vault-1", 0) == 0


def test_unlock_with_pin_invalid_then_lockout(client, vault_repo, pin_deps):
    hasher, tracker = pin_deps
    _set_vault_owner(vault_repo, "demo-vault-1", "test-user-id")
    vault_repo.update_pin(
        "demo-vault-1",
        hasher.hash(PIN("827364")),
        datetime.now(timezone.utc),
    )

    resp1 = client.post("/api/v1/vaults/demo-vault-1/unlock/pin", json={"pin": "135791"})
    assert resp1.status_code == 401
    assert tracker.counts["demo-vault-1"] == 1

    resp2 = client.post("/api/v1/vaults/demo-vault-1/unlock/pin", json={"pin": "135791"})
    assert resp2.status_code == 423
    assert tracker.counts["demo-vault-1"] == 2
