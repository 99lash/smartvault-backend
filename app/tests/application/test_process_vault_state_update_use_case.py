import pytest
import asyncio
from datetime import datetime, timezone
from app.application.use_cases.process_vault_state_update import ProcessVaultStateUpdate
from app.infrastructure.db.repositories.in_memory_vault_repository import InMemoryVaultRepository
from app.domain.value_objects.vault_status import VaultStatus

@pytest.mark.asyncio
async def test_process_vault_state_update_success():
    repo = InMemoryVaultRepository()
    use_case = ProcessVaultStateUpdate(repo)
    
    vault_id = "demo-vault-1"
    new_status = "UNLOCKED"
    
    # Pre-condition check
    initial_vault = repo.get_by_id(vault_id)
    assert initial_vault.status == VaultStatus.LOCKED
    
    result = await use_case.execute(
        vault_id=vault_id,
        new_status=new_status,
        metadata={"source": "test"}
    )
    
    # Assert result
    assert result.vault.id == vault_id
    assert result.vault.status == VaultStatus.UNLOCKED
    assert result.previous_status == VaultStatus.LOCKED
    
    # Assert persistence
    updated_vault = repo.get_by_id(vault_id)
    assert updated_vault.status == VaultStatus.UNLOCKED
    assert updated_vault.last_seen_at is not None
