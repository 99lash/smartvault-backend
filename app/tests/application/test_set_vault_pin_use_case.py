from datetime import datetime, timezone

import pytest

from app.application.use_cases.set_vault_pin import SetVaultPIN, SetVaultPINInput
from app.domain.exceptions import InvalidPINError, VaultNotFoundError
from app.domain.value_objects.pin import PIN
from app.infrastructure.db.repositories.in_memory_vault_repository import InMemoryVaultRepository
from app.application.ports.pin_hasher import PINHasher


class _FakeHasher(PINHasher):
    def hash(self, pin: PIN) -> str:
        return f"hash:{pin.value}"

    def verify(self, pin: PIN, hashed_pin: str) -> bool:
        return hashed_pin == f"hash:{pin.value}"


def test_set_vault_pin_success():
    repo = InMemoryVaultRepository()
    hasher = _FakeHasher()
    uc = SetVaultPIN(repo, hasher)

    result = uc.execute(SetVaultPINInput(vault_id="demo-vault-1", pin="827364"))

    assert result.vault.pin_hash == "hash:827364"
    assert result.vault.pin_set_at is not None
    assert isinstance(result.vault.pin_set_at, datetime)
    assert result.vault.pin_set_at.tzinfo is not None  # aware


def test_set_vault_pin_invalid_pin_raises():
    repo = InMemoryVaultRepository()
    hasher = _FakeHasher()
    uc = SetVaultPIN(repo, hasher)

    with pytest.raises(InvalidPINError):
        uc.execute(SetVaultPINInput(vault_id="demo-vault-1", pin="111111"))  # weak pattern


def test_set_vault_pin_missing_vault_raises():
    repo = InMemoryVaultRepository()
    hasher = _FakeHasher()
    uc = SetVaultPIN(repo, hasher)

    with pytest.raises(VaultNotFoundError):
        uc.execute(SetVaultPINInput(vault_id="missing", pin="827364"))
