from abc import ABC, abstractmethod
from app.domain.models.vault import Vault


class VaultRepository(ABC):
    @abstractmethod
    def get_by_id(self, vault_id: str) -> Vault | None:
        raise NotImplementedError
