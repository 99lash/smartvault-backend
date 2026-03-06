from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass

from app.application.ports.vault_repository import VaultRepository
from app.application.ports.websocket_manager import WebSocketManagerPort
from app.core.logging import get_logger
from app.domain.exceptions import UnauthorizedVaultAccessError, VaultNotFoundError

logger = get_logger(__name__)


@dataclass
class DeleteVaultInput:
    vault_id: str
    requesting_user_id: str


class DeleteVault:
    def __init__(self, vault_repo: VaultRepository, ws_manager: WebSocketManagerPort) -> None:
        self._vault_repo = vault_repo
        self._ws_manager = ws_manager

    def execute(self, input: DeleteVaultInput) -> None:
        vault = self._vault_repo.get_by_id(input.vault_id)
        if vault is None:
            raise VaultNotFoundError(input.vault_id)

        if vault.owner_id != input.requesting_user_id:
            raise UnauthorizedVaultAccessError(input.requesting_user_id, input.vault_id)

        async def _notify_if_online() -> None:
            online_result = self._ws_manager.is_vault_online(vault.id)
            online = await online_result if inspect.isawaitable(online_result) else online_result
            if not online:
                return
            send_result = self._ws_manager.send_to_vault(vault.id, {"command": "reset"})
            if inspect.isawaitable(send_result):
                await send_result

        try:
            asyncio.create_task(_notify_if_online())
        except Exception:
            logger.warning("delete_vault_ws_notify_failed", vault_id=vault.id)

        self._vault_repo.delete(input.vault_id)
        logger.info("vault_deleted", vault_id=input.vault_id, user_id=input.requesting_user_id)
