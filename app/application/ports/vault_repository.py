from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.models.vault import Vault


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
