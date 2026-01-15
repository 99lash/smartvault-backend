from abc import ABC, abstractmethod
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
