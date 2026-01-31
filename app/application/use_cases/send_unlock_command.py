"""
Send unlock command to vault device via WebSocket.

This use case:
1. Verifies user is authorized
2. Creates signed command
3. Sends command to vault via WebSocket
4. Returns command ID for tracking
"""

import hashlib
import hmac
import secrets
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.application.ports.vault_repository import VaultRepository
from app.core.settings import settings
from app.domain.value_objects.websocket_messages import CommandAction, MessageType
from app.infrastructure.messaging.websocket_manager import manager


@dataclass
class SendUnlockCommandResult:
    command_id: str
    vault_id: str
    expires_at: datetime
    sent: bool  # True if vault is online, False if offline


class VaultOfflineError(Exception):
    """Raised when vault is not connected"""


class SendUnlockCommand:
    def __init__(self, repo: VaultRepository):
        self._repo = repo

    def execute(
        self,
        *,
        vault_id: str,
        user_id: str,
    ) -> SendUnlockCommandResult:
        """
        Send unlock command to vault device.

        Args:
            vault_id: ID of vault to unlock
            user_id: ID of user requesting unlock

        Returns:
            Result with command_id and status

        Raises:
            ValueError: If vault not found or user not authorized
            VaultOfflineError: If vault is not connected
        """

        # 1. Verify vault exists
        vault = self._repo.get_by_id(vault_id)
        if vault is None:
            raise ValueError(f"Vault {vault_id} not found")

        # 2. Verify user is authorized (owner or has access)
        # TODO: Check VaultAuthorization table
        if vault.owner_id != user_id:
            # For now, only owner can unlock
            # Later: check vault_authorizations table
            raise ValueError(f"User {user_id} not authorized for vault {vault_id}")

        # 3. Check if vault is online
        if not manager.is_vault_online(vault_id):
            raise VaultOfflineError(f"Vault {vault_id} is offline")

        # 4. Create signed command
        command_id = f"cmd_{uuid4()}"
        timestamp = datetime.now(timezone.utc)
        expires_at = timestamp + timedelta(seconds=30)  # 30 second expiry
        nonce = secrets.token_hex(16)

        # Create command payload
        command_data = {
            "command_id": command_id,
            "action": CommandAction.UNLOCK.value,
            "vault_id": vault_id,
            "timestamp": timestamp.isoformat(),
            "expires_at": expires_at.isoformat(),
            "nonce": nonce,
        }

        # Sign the command (HMAC-SHA256)
        signature = self._sign_command(command_data)
        command_data["signature"] = signature

        # 5. Send command via WebSocket
        message = {
            "type": MessageType.COMMAND.value,
            "payload": command_data,
        }

        try:
            asyncio.create_task(manager.send_to_vault(vault_id, message))
            sent = True
        except Exception as e:
            raise VaultOfflineError(f"Failed to send command: {e}")

        # 6. TODO: Log command in activity log

        return SendUnlockCommandResult(
            command_id=command_id,
            vault_id=vault_id,
            expires_at=expires_at,
            sent=sent,
        )

    def _sign_command(self, command_data: dict) -> str:
        """
        Sign command with HMAC-SHA256.

        The signature prevents tampering and replay attacks.
        Vault device will verify signature before executing.
        """
        # Create canonical string to sign
        canonical = (
            f"{command_data['command_id']}"
            f"{command_data['action']}"
            f"{command_data['vault_id']}"
            f"{command_data['timestamp']}"
            f"{command_data['expires_at']}"
            f"{command_data['nonce']}"
        )

        # Sign with secret key
        signature = hmac.new(
            settings.VAULT_COMMAND_SECRET.encode("utf-8"),
            canonical.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return signature
