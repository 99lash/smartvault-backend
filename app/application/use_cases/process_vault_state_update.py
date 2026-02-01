"""
Process state updates from vault devices.
Updates vault status in database and creates activity log.
"""

from datetime import datetime, timezone
from dataclasses import dataclass

from app.application.ports.vault_repository import VaultRepository
from app.domain.models.vault import Vault
from app.domain.value_objects.vault_status import VaultStatus


@dataclass
class ProcessVaultStateUpdateResult:
    vault: Vault
    previous_status: VaultStatus


class ProcessVaultStateUpdate:
    def __init__(self, repo: VaultRepository):
        self._repo = repo

    async def execute(
        self,
        *,
        vault_id: str,
        new_status: str,
        metadata: dict,
    ) -> ProcessVaultStateUpdateResult:
        """
        Process a state update from a vault device.

        Steps:
        1. Get current vault state
        2. Update vault status
        3. Update last_seen_at
        4. Create activity log entry
        5. Return result
        """

        # Get current vault
        vault = self._repo.get_by_id(vault_id)
        if vault is None:
            raise ValueError(f"Vault {vault_id} not found")

        previous_status = vault.status

        # Update vault status
        updated_vault = Vault(
            id=vault.id,
            owner_id=vault.owner_id,
            hardware_uuid=vault.hardware_uuid,
            vault_name=vault.vault_name,
            status=VaultStatus(new_status),
            last_seen_at=datetime.now(timezone.utc),
        )

        # Save to repository
        self._repo.update(updated_vault)

        # TODO: Create activity log entry
        # log_entry = AccessLog(
        #     id=f"log_{uuid4()}",
        #     vault_id=vault_id,
        #     user_id=None,  # System-triggered
        #     action="STATE_CHANGE",
        #     method="SYSTEM",
        #     timestamp=datetime.now(timezone.utc),
        #     metadata={
        #         "previous_status": previous_status.value,
        #         "new_status": new_status,
        #         **metadata,
        #     },
        # )
        # self._log_repo.create(log_entry)

        return ProcessVaultStateUpdateResult(
            vault=updated_vault,
            previous_status=previous_status,
        )
