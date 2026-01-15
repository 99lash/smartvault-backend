from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from app.domain.models.vault import Vault
from app.domain.value_objects.vault_status import VaultStatus


def test_vault_status_enum_values() -> None:
    assert VaultStatus.LOCKED.value == "LOCKED"
    assert VaultStatus.UNLOCKED.value == "UNLOCKED"
    assert VaultStatus.OFFLINE.value == "OFFLINE"


def test_vault_is_frozen_dataclass() -> None:
    now = datetime.now(timezone.utc)
    vault = Vault(
        id="vault-123",
        owner_id="owner-1",
        hardware_uuid="HW-123",
        nickname="Bedroom Vault",
        status=VaultStatus.LOCKED,
        last_seen_at=now,
    )

    assert vault.id == "vault-123"
    assert vault.owner_id == "owner-1"
    assert vault.hardware_uuid == "HW-123"
    assert vault.nickname == "Bedroom Vault"
    assert vault.status is VaultStatus.LOCKED
    assert vault.last_seen_at == now

    try:
        vault.status = VaultStatus.UNLOCKED
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("Vault should be immutable (frozen dataclass).")
