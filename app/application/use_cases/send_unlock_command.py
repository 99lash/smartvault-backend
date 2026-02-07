"""
Send Unlock Command Use Case

Dispatches signed unlock commands to vault devices via WebSocket.
Handles authorization, command signing, and delivery confirmation.

Security Features:
- Role-based authorization (only authorized users can unlock)
- HMAC-SHA256 command signing (prevents tampering)
- Nonce-based replay attack prevention
- Time-limited commands (30 second expiry)
"""

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.application.ports.vault_repository import VaultRepository
from app.application.use_cases.check_vault_access import CheckVaultAccess
from app.core.settings import settings
from app.domain.exceptions import InsufficientPermissionsError, UnauthorizedVaultAccessError
from app.domain.value_objects.websocket_messages import CommandAction, MessageType
from app.infrastructure.messaging.websocket_manager import manager


@dataclass
class SendUnlockCommandResult:
    """
    Result of sending an unlock command.

    Attributes:
        command_id: Unique identifier for tracking the command.
        vault_id: The vault that received the command.
        expires_at: Timestamp when the command expires.
        sent: True if vault was online and received the command.
    """
    command_id: str
    vault_id: str
    expires_at: datetime
    sent: bool


class VaultOfflineError(Exception):
    """
    Raised when the vault device is not connected.

    This indicates the WebSocket connection to the vault is unavailable.
    """


class SendUnlockCommand:
    """
    Use case for sending unlock commands to vault devices.

    Flow:
    1. Verify vault exists
    2. Verify user has unlock permission (role-based)
    3. Verify vault is online
    4. Create signed command payload
    5. Send via WebSocket
    6. Return command tracking info
    """

    # Command expiry time in seconds
    COMMAND_EXPIRY_SECONDS = 30

    def __init__(
        self,
        repo: VaultRepository,
        check_access: CheckVaultAccess
    ):
        """
        Initialize the use case with required dependencies.

        Args:
            repo: Repository to fetch vault data.
            check_access: Use case for authorization checks.
        """
        self._repo = repo
        self._check_access = check_access

    async def execute(
        self,
        *,
        vault_id: str,
        user_id: str,
    ) -> SendUnlockCommandResult:
        """
        Send an unlock command to a vault device.

        This method performs authorization checks before creating and
        sending the signed command.

        Args:
            vault_id: ID of the vault to unlock.
            user_id: ID of the user requesting the unlock.

        Returns:
            SendUnlockCommandResult with tracking information.

        Raises:
            ValueError: If vault not found.
            UnauthorizedVaultAccessError: If user has no vault access.
            InsufficientPermissionsError: If user's role cannot unlock.
            VaultOfflineError: If vault is not connected.
        """
        # Step 1: Verify vault exists
        vault = self._repo.get_by_id(vault_id)
        if vault is None:
            raise ValueError(f"Vault {vault_id} not found")

        # Step 2: Verify user has authorization to unlock
        access_info = self._check_access.execute(vault_id, user_id)
        if not access_info.has_access:
            raise UnauthorizedVaultAccessError(user_id, vault_id)

        # Step 3: Verify user's role permits unlocking
        # (OWNER can always unlock, role check for members)
        if access_info.role and not access_info.role.can_unlock():
            raise InsufficientPermissionsError(
                user_id=user_id,
                vault_id=vault_id,
                role=access_info.role.value,
                required_action="unlock_vault",
            )

        # Step 4: Verify vault is connected and can receive commands
        if not manager.is_vault_online(vault_id):
            raise VaultOfflineError(
                f"Vault {vault_id} is offline. Commands can only be sent "
                "to connected devices."
            )

        # Step 5: Create the command payload
        command_id = f"cmd_{uuid4()}"
        timestamp = datetime.now(timezone.utc)
        expires_at = timestamp + timedelta(seconds=self.COMMAND_EXPIRY_SECONDS)
        nonce = secrets.token_hex(16)  # Random bytes for replay protection

        # Build the command data structure
        command_data = {
            "command_id": command_id,
            "action": CommandAction.UNLOCK.value,
            "vault_id": vault_id,
            "timestamp": timestamp.isoformat(),
            "expires_at": expires_at.isoformat(),
            "nonce": nonce,
        }

        # Step 6: Sign the command to prevent tampering
        # The vault device will verify this signature before executing
        signature = self._sign_command(command_data)
        command_data["signature"] = signature

        # Step 7: Send command via WebSocket connection
        message = {
            "type": MessageType.COMMAND.value,
            "payload": command_data,
        }

        try:
            await manager.send_to_vault(vault_id, message)
            sent = True
        except Exception as e:
            raise VaultOfflineError(f"Failed to send command: {e}")

        # TODO: Step 8: Log command in activity audit trail
        # This should record: command_id, user_id, vault_id, timestamp, result

        return SendUnlockCommandResult(
            command_id=command_id,
            vault_id=vault_id,
            expires_at=expires_at,
            sent=sent,
        )

    def _sign_command(self, command_data: dict) -> str:
        """
        Create HMAC-SHA256 signature for the command.

        Security Purpose:
        - Ensures command wasn't modified in transit
        - Prevents replay attacks (nonce + timestamp + expiry)
        - Vault device can verify authenticity before executing

        Args:
            command_data: The command payload to sign.

        Returns:
            Hexadecimal signature string.
        """
        # Build canonical string from command fields
        # Order matters: must match vault device's verification logic
        canonical = "\n".join(
            [
                command_data["command_id"],
                command_data["action"],
                command_data["vault_id"],
                command_data["timestamp"],
                command_data["expires_at"],
                command_data["nonce"],
            ]
        )

        # Generate HMAC-SHA256 signature using the command secret
        signature = hmac.new(
            settings.VAULT_COMMAND_SECRET.encode("utf-8"),
            canonical.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return signature
