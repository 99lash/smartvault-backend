import pytest

from app.application.use_cases.provision_vault import ProvisionVault, HardwareAlreadyProvisioned
from app.domain.models.vault import Vault
from app.domain.value_objects.vault_status import VaultStatus
from app.infrastructure.db.repositories.in_memory_vault_repository import InMemoryVaultRepository


def _make_repo_with_vault(hardware_uuid: str, status: VaultStatus) -> InMemoryVaultRepository:
    """Return a fresh repo containing a single vault with the given UUID and status."""
    repo = InMemoryVaultRepository()
    vault = Vault(
        id="vault-existing-001",
        owner_id="user-001",
        hardware_uuid=hardware_uuid,
        vault_name="Existing Vault",
        status=status,
    )
    # Bypass create() uniqueness check by inserting directly
    repo._vaults[vault.id] = vault
    return repo


def test_new_device_provisions_successfully():
    repo = InMemoryVaultRepository()
    uc = ProvisionVault(repo)

    result = uc.execute(
        owner_id="user-001",
        hardware_uuid="hw-brand-new",
        vault_name="My Vault",
    )

    assert result.vault.hardware_uuid == "hw-brand-new"
    assert result.vault.status == VaultStatus.LOCKED
    assert result.vault.vault_name == "My Vault"


def test_active_vault_raises_hardware_already_provisioned():
    repo = _make_repo_with_vault("hw-active", VaultStatus.LOCKED)
    uc = ProvisionVault(repo)

    with pytest.raises(HardwareAlreadyProvisioned):
        uc.execute(
            owner_id="user-001",
            hardware_uuid="hw-active",
            vault_name="Should Fail",
        )


def test_unlocked_vault_raises_hardware_already_provisioned():
    repo = _make_repo_with_vault("hw-unlocked", VaultStatus.UNLOCKED)
    uc = ProvisionVault(repo)

    with pytest.raises(HardwareAlreadyProvisioned):
        uc.execute(
            owner_id="user-001",
            hardware_uuid="hw-unlocked",
            vault_name="Should Fail",
        )


def test_reset_vault_reprovisions_in_place():
    repo = _make_repo_with_vault("hw-reset", VaultStatus.PROVISIONING)
    uc = ProvisionVault(repo)

    result = uc.execute(
        owner_id="user-001",
        hardware_uuid="hw-reset",
        vault_name="Updated Name",
    )

    assert result.vault.id == "vault-existing-001"       # same vault_id preserved
    assert result.vault.status == VaultStatus.LOCKED      # active again
    assert result.vault.vault_name == "Updated Name"      # name updated
    assert result.vault.pin_hash is None                  # cleared
    assert result.vault.pin_set_at is None                # cleared


def test_reset_vault_preserves_existing_name_when_none_given():
    repo = _make_repo_with_vault("hw-reset", VaultStatus.PROVISIONING)
    uc = ProvisionVault(repo)

    result = uc.execute(
        owner_id="user-001",
        hardware_uuid="hw-reset",
        vault_name=None,
    )

    assert result.vault.id == "vault-existing-001"
    assert result.vault.vault_name == "Existing Vault"    # falls back to existing name
