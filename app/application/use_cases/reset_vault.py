"""
Reset a vault to provisioning state.

Wipes vault credentials and state in-place (same vault_id).
Deletes access logs for the vault.
Sends reset command to firmware via WebSocket if online.
"""

from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass

from app.application.ports.activity_log_repository import ActivityLogRepository
from app.application.ports.vault_repository import VaultRepository
from app.application.ports.websocket_manager import WebSocketManagerPort
from app.core.logging import get_logger
from app.domain.models.vault import Vault
from app.domain.value_objects.vault_status import VaultStatus

logger = get_logger(__name__)


class VaultNotFoundError(Exception):
    pass


class UnauthorizedVaultAccessError(Exception):
    pass


@dataclass
class ResetVaultInput:
    vault_id: str
    requesting_user_id: str


@dataclass
class ResetVaultResult:
    vault_id: str


class ResetVault:
    def __init__(
        self,
        vault_repo: VaultRepository,
        log_repo: ActivityLogRepository,
        ws_manager: WebSocketManagerPort,
    ) -> None:
        self._vault_repo = vault_repo
        self._log_repo = log_repo
        self._ws_manager = ws_manager

    def execute(self, input: ResetVaultInput) -> ResetVaultResult:
        vault = self._vault_repo.get_by_id(input.vault_id)
        if vault is None:
            raise VaultNotFoundError(f"Vault {input.vault_id} not found")

        if vault.owner_id != input.requesting_user_id:
            raise UnauthorizedVaultAccessError("Only the vault owner can reset the vault")

        reset_vault = Vault(
            id=vault.id,
            owner_id=vault.owner_id,
            hardware_uuid=vault.hardware_uuid,
            vault_name=vault.vault_name,
            status=VaultStatus.PROVISIONING,
            last_seen_at=None,
            pin_hash=None,
            pin_set_at=None,
        )
        self._vault_repo.update(reset_vault)

        try:
            self._log_repo.delete_by_vault_id(input.vault_id)
        except Exception:
            logger.warning("reset_vault_log_delete_failed", vault_id=input.vault_id)

        async def _send_reset_if_online() -> None:
            online_result = self._ws_manager.is_vault_online(vault.id)
            online = await online_result if inspect.isawaitable(online_result) else online_result
            if not online:
                return

            send_result = self._ws_manager.send_to_vault(vault.id, {"command": "reset"})
            if inspect.isawaitable(send_result):
                await send_result

        try:
            asyncio.create_task(_send_reset_if_online())
        except Exception:
            logger.warning("reset_command_send_failed", vault_id=vault.id)

        logger.info("vault_reset", vault_id=vault.id, user_id=input.requesting_user_id)

        return ResetVaultResult(vault_id=vault.id)
