"""
Register a device during firmware provisioning.

Called by firmware POST /devices/register after captive portal.
Validates provisioning token, provisions vault, clears token.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.ports.provisioning_token_store import ProvisioningTokenStore
from app.application.ports.user_repository import UserRepository
from app.application.ports.vault_repository import VaultRepository
from app.application.use_cases.provision_vault import HardwareAlreadyProvisioned, ProvisionVault
from app.core.logging import get_logger

logger = get_logger(__name__)


class InvalidProvisioningTokenError(Exception):
    """Raised when provisioning token is not found or already used."""


class HardwareAlreadyRegisteredError(Exception):
    """Raised when hardware_uuid is already registered to a vault."""


@dataclass
class RegisterDeviceInput:
    hardware_uuid: str
    provisioning_token: str


@dataclass
class RegisterDeviceResult:
    vault_id: str
    vault_name: str | None


class RegisterDevice:
    def __init__(
        self,
        token_store: ProvisioningTokenStore,
        user_repo: UserRepository,
        vault_repo: VaultRepository,
    ) -> None:
        self._token_store = token_store
        self._user_repo = user_repo
        self._vault_repo = vault_repo

    async def execute(self, input: RegisterDeviceInput) -> RegisterDeviceResult:
        user_id = await self._token_store.get(input.provisioning_token)
        if user_id is None:
            raise InvalidProvisioningTokenError("Invalid or expired provisioning token")

        user = self._user_repo.get_by_id(user_id)
        if user is None:
            raise InvalidProvisioningTokenError("Invalid or expired provisioning token")

        provision = ProvisionVault(self._vault_repo)
        try:
            result = provision.execute(
                owner_id=user.id,
                hardware_uuid=input.hardware_uuid,
                vault_name=None,
            )
        except HardwareAlreadyProvisioned as exc:
            raise HardwareAlreadyRegisteredError(
                f"Hardware {input.hardware_uuid} is already registered - reset the vault first"
            ) from exc

        await self._token_store.delete(input.provisioning_token)

        logger.info("device_registered", vault_id=result.vault.id, user_id=user.id)

        return RegisterDeviceResult(
            vault_id=result.vault.id,
            vault_name=result.vault.vault_name,
        )
