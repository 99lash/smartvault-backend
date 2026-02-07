"""Port for sending commands to vault devices via WebSocket."""

from abc import ABC, abstractmethod


class WebSocketManagerPort(ABC):
    """Port for sending commands to vault devices via WebSocket."""

    @abstractmethod
    async def is_vault_online(self, vault_id: str) -> bool:
        """
        Check if vault device is connected.

        Args:
            vault_id: The vault to check.

        Returns:
            True if the vault is online and can receive commands.
        """
        ...

    @abstractmethod
    async def send_to_vault(self, vault_id: str, message: dict) -> None:
        """
        Send a message to a vault device.

        Args:
            vault_id: The target vault.
            message: The message payload to send.

        Raises:
            VaultOfflineError: If the vault is not connected.
        """
        ...
