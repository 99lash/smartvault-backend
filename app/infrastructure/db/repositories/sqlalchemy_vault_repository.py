from datetime import datetime

from sqlalchemy.orm import Session

from app.application.ports.vault_repository import VaultRepository
from app.infrastructure.db.models.vault_orm import VaultORM
from app.domain.models.vault import Vault
from app.domain.value_objects.vault_status import VaultStatus

# lipat nalang sa use case or domain kung business rule error na.
# ang tingin ko ngayon dito ay data integrity error kaya dito ko muna nilagay
class InvalidVaultStatusError(Exception):
    """Raised when the database contains an invalid vault status string."""
    def __init__(self, vault_id: str, invalid_status: str):
        self.vault_id = vault_id
        self.invalid_status = invalid_status
        super().__init__(f"Invalid status '{invalid_status}' for vault '{vault_id}'")


class SqlAlchemyVaultRepository(VaultRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    # private method; vault domain mapper
    def _to_domain(self, row: VaultORM) -> Vault:
        try:
            status = VaultStatus(row.status)
        except ValueError as e:
            raise InvalidVaultStatusError(row.id, row.status) from e

        return Vault(
            id=row.id,
            owner_id=row.owner_id,
            hardware_uuid=row.hardware_uuid,
            vault_name=row.vault_name,
            status=status,
            last_seen_at=row.last_seen_at,
            pin_hash=row.pin_hash,
            pin_set_at=row.pin_set_at,
        )
        
    def get_by_id(self, vault_id: str) -> Vault | None:
        row = self._session.get(VaultORM, vault_id)
        if row is None:
            return None

        return self._to_domain(row)
        
    def get_by_hardware_uuid(self, hardware_uuid: str) -> Vault | None:
        row = (
            self._session.query(VaultORM)
            .filter(VaultORM.hardware_uuid == hardware_uuid)
            .one_or_none()
        )
        if row is None:
            return None

        return self._to_domain(row)
        
    def create(self, vault: Vault) -> Vault:
        row = VaultORM(
            id=vault.id,
            owner_id=vault.owner_id,
            hardware_uuid=vault.hardware_uuid,
            vault_name=vault.vault_name,
            status=vault.status.value,
            last_seen_at=vault.last_seen_at,
            pin_hash=vault.pin_hash,
            pin_set_at=vault.pin_set_at,
        )

        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)

        return self._to_domain(row)

    def update(self, vault: Vault) -> Vault:
        row = self._session.get(VaultORM, vault.id)
        if row is None:
            raise ValueError(f"Vault {vault.id} not found")

        row.owner_id = vault.owner_id
        row.hardware_uuid = vault.hardware_uuid
        row.vault_name = vault.vault_name
        row.status = vault.status.value
        row.last_seen_at = vault.last_seen_at
        row.pin_hash = vault.pin_hash
        row.pin_set_at = vault.pin_set_at

        self._session.commit()
        self._session.refresh(row)

        return self._to_domain(row)

    def update_pin(self, vault_id: str, pin_hash: str, pin_set_at: datetime) -> Vault:
        row = self._session.get(VaultORM, vault_id)
        if row is None:
            raise ValueError(f"Vault {vault_id} not found")

        row.pin_hash = pin_hash
        row.pin_set_at = pin_set_at

        self._session.commit()
        self._session.refresh(row)

        return self._to_domain(row)


