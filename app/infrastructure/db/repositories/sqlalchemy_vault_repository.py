from sqlalchemy.orm import Session

from app.application.ports.vault_repository import VaultRepository
from app.infrastructure.db.models.vault_orm import VaultORM
from app.domain.models.vault import Vault
from app.domain.value_objects.vault_status import VaultStatus


class SqlAlchemyVaultRepository(VaultRepository):
    def __init__(self, session: Session) -> None:
        self._session = session
        
    def get_by_id(self, vault_id: str) -> Vault | None:
        row = self._session.get(VaultORM, vault_id)
        if row is None:
            return None

        return Vault(
            id=row.id,
            owner_id=row.owner_id,
            hardware_uuid=row.hardware_uuid,
            vault_name=row.vault_name,
            status=VaultStatus(row.status),
            last_seen_at=row.last_seen_at,
        )
        
    def get_by_hardware_uuid(self, hardware_uuid: str) -> Vault | None:
        row = (
            self._session.query(VaultORM)
            .filter(VaultORM.hardware_uuid == hardware_uuid)
            .one_or_none()
        )
        if row is None:
            return None

        return Vault(
            id=row.id,
            owner_id=row.owner_id,
            hardware_uuid=row.hardware_uuid,
            vault_name=row.vault_name,
            status=VaultStatus(row.status),
            last_seen_at=row.last_seen_at,
        )
        
    def create(self, vault: Vault) -> Vault:
        row = VaultORM(
            id=vault.id,
            owner_id=vault.owner_id,
            hardware_uuid=vault.hardware_uuid,
            vault_name=vault.vault_name,
            status=vault.status.value,
            last_seen_at=vault.last_seen_at,
        )

        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)

        return Vault(
            id=row.id,
            owner_id=row.owner_id,
            hardware_uuid=row.hardware_uuid,
            vault_name=row.vault_name,
            status=VaultStatus(row.status),
            last_seen_at=row.last_seen_at,
        )

    def update(self, vault: Vault) -> Vault:
        row = self._session.get(VaultORM, vault.id)
        if row is None:
            raise ValueError(f"Vault {vault.id} not found")

        row.owner_id = vault.owner_id
        row.hardware_uuid = vault.hardware_uuid
        row.vault_name = vault.vault_name
        row.status = vault.status.value
        row.last_seen_at = vault.last_seen_at

        self._session.commit()
        self._session.refresh(row)

        return Vault(
            id=row.id,
            owner_id=row.owner_id,
            hardware_uuid=row.hardware_uuid,
            vault_name=row.vault_name,
            status=VaultStatus(row.status),
            last_seen_at=row.last_seen_at,
        )


