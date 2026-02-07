from datetime import datetime, timezone

import pytest

from app.application.use_cases.unlock_vault_with_pin import (
    UnlockVaultWithPIN,
    UnlockVaultWithPINInput,
)
from app.domain.exceptions import InvalidPINError, PINLockedOutError, PINNotSetError, VaultNotFoundError
from app.domain.value_objects.pin import PIN
from app.domain.value_objects.pin_attempt_result import PINAttemptResult
from app.infrastructure.db.repositories.in_memory_vault_repository import InMemoryVaultRepository
from app.application.ports.pin_hasher import PINHasher
from app.application.ports.pin_attempt_tracker import PINAttemptTracker


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


@pytest.mark.asyncio
async def test_unlock_success_resets_counter():
    repo = InMemoryVaultRepository()
    hasher = _FakeHasher()
    tracker = _FakeTracker(max_attempts=2)
    vault = repo.update_pin(
        "demo-vault-1",
        hasher.hash(PIN("827364")),
        pin_set_at=datetime.now(timezone.utc),
    )

    uc = UnlockVaultWithPIN(repo, hasher, tracker)
    result = await uc.execute(UnlockVaultWithPINInput(vault_id=vault.id, pin="827364"))

    assert result.result is PINAttemptResult.SUCCESS
    assert tracker.counts.get(vault.id, 0) == 0


@pytest.mark.asyncio
async def test_unlock_invalid_pin_increments_and_returns_remaining():
    repo = InMemoryVaultRepository()
    hasher = _FakeHasher()
    tracker = _FakeTracker(max_attempts=3)
    vault = repo.update_pin(
        "demo-vault-1",
        hasher.hash(PIN("827364")),
        pin_set_at=datetime.now(timezone.utc),
    )

    uc = UnlockVaultWithPIN(repo, hasher, tracker)

    with pytest.raises(InvalidPINError):
        await uc.execute(UnlockVaultWithPINInput(vault_id=vault.id, pin="135791"))

    assert tracker.counts[vault.id] == 1


@pytest.mark.asyncio
async def test_unlock_lockout_after_max_attempts():
    repo = InMemoryVaultRepository()
    hasher = _FakeHasher()
    tracker = _FakeTracker(max_attempts=2)
    vault = repo.update_pin(
        "demo-vault-1",
        hasher.hash(PIN("827364")),
        pin_set_at=datetime.now(timezone.utc),
    )

    uc = UnlockVaultWithPIN(repo, hasher, tracker)

    with pytest.raises(InvalidPINError):
        await uc.execute(UnlockVaultWithPINInput(vault_id=vault.id, pin="135791"))

    with pytest.raises(PINLockedOutError):
        await uc.execute(UnlockVaultWithPINInput(vault_id=vault.id, pin="135791"))

    assert tracker.counts[vault.id] == 2


@pytest.mark.asyncio
async def test_unlock_when_pin_not_set_raises():
    repo = InMemoryVaultRepository()
    hasher = _FakeHasher()
    tracker = _FakeTracker()
    uc = UnlockVaultWithPIN(repo, hasher, tracker)

    with pytest.raises(PINNotSetError):
        await uc.execute(UnlockVaultWithPINInput(vault_id="demo-vault-1", pin="827364"))


@pytest.mark.asyncio
async def test_unlock_missing_vault_raises():
    repo = InMemoryVaultRepository()
    hasher = _FakeHasher()
    tracker = _FakeTracker()
    uc = UnlockVaultWithPIN(repo, hasher, tracker)

    with pytest.raises(VaultNotFoundError):
        await uc.execute(UnlockVaultWithPINInput(vault_id="missing", pin="827364"))
