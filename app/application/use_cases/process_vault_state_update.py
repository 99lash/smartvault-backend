"""
Process state updates from vault devices.
Updates vault status in database and creates activity log.
"""

from datetime import datetime, timezone
from dataclasses import dataclass

from app.application.ports.activity_log_repository import ActivityLogRepository
from app.application.ports.vault_repository import VaultRepository
from app.application.use_cases.log_activity import LogActivity, LogActivityInput
from app.core.logging import get_logger
from app.domain.models.vault import Vault
from app.domain.value_objects.vault_status import VaultStatus

logger = get_logger(__name__)


@dataclass
class ProcessVaultStateUpdateResult:
    vault: Vault
    previous_status: VaultStatus


class ProcessVaultStateUpdate:
    def __init__(self, repo: VaultRepository, log_repo: ActivityLogRepository | None = None):
        self._repo = repo
        self._log_activity = LogActivity(log_repo) if log_repo else None

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
            pin_hash=vault.pin_hash,
            pin_set_at=vault.pin_set_at,
        )

        # Save to repository
        self._repo.update(updated_vault)

        # Log the state change — fire-and-forget; never crash the main operation
        if self._log_activity:
            try:
                self._log_activity.execute(LogActivityInput(
                    vault_id=vault_id,
                    action="VAULT_STATE_CHANGED",
                    method="SYSTEM",
                    user_id=None,
                    metadata={
                        "previous_status": previous_status.value,
                        "new_status": new_status,
                        **metadata,
                    },
                ))
            except Exception:
                logger.warning("activity_log_failed", vault_id=vault_id, action="VAULT_STATE_CHANGED")

        return ProcessVaultStateUpdateResult(
            vault=updated_vault,
            previous_status=previous_status,
        )
