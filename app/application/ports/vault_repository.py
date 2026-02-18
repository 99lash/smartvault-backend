from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.models.vault import Vault
from app.domain.models.vault_access_summary import VaultAccessSummary


class VaultAlreadyExistsError(Exception):
    """Raised when a vault with the same unique identifier already exists."""
    pass


class VaultRepository(ABC):
    @abstractmethod
    def get_by_id(self, vault_id: str) -> Vault | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_hardware_uuid(self, hardware_uuid: str) -> Vault | None:
        raise NotImplementedError

    @abstractmethod
    def create(self, vault: Vault) -> Vault:
        raise NotImplementedError

    @abstractmethod
    def update(self, vault: Vault) -> Vault:
        raise NotImplementedError

    @abstractmethod
    def update_pin(self, vault_id: str, pin_hash: str, pin_set_at: datetime) -> Vault:
        """
        Update the stored PIN hash and timestamp for a vault.
        Returns the updated Vault.
        """
        raise NotImplementedError

    @abstractmethod
    def list_for_user(self, user_id: str) -> list[VaultAccessSummary]:
        """List vaults a user owns or has access to."""
        raise NotImplementedError
