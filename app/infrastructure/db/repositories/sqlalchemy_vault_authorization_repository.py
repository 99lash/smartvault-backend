from __future__ import annotations
from datetime import datetime, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.application.ports.vault_authorization_repository import VaultAuthorizationRepository
from app.domain.models.vault_authorization import VaultAuthorization
from app.domain.value_objects.vault_role import VaultRole
from app.infrastructure.db.models.vault_authorization_orm import VaultAuthorizationORM


class SqlAlchemyVaultAuthorizationRepository(VaultAuthorizationRepository):
    def __init__(self, db: Session):
        self._db = db

    def _to_domain(self, orm: VaultAuthorizationORM) -> VaultAuthorization:
        return VaultAuthorization(
            id=orm.id,
            vault_id=orm.vault_id,
            user_id=orm.user_id,
            role=VaultRole(orm.role),
            granted_by=orm.granted_by,
            granted_at=orm.granted_at,
        )

    def create(self, auth: VaultAuthorization) -> VaultAuthorization:
        orm = VaultAuthorizationORM(
            id=auth.id,
            vault_id=auth.vault_id,
            user_id=auth.user_id,
            role=auth.role.value,
            granted_by=auth.granted_by,
            granted_at=auth.granted_at,
        )
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return self._to_domain(orm)

    def update_role(self, vault_id: str, user_id: str, role: VaultRole) -> VaultAuthorization | None:
        stmt = (
            update(VaultAuthorizationORM)
            .where(
                VaultAuthorizationORM.vault_id == vault_id,
                VaultAuthorizationORM.user_id == user_id
            )
            .values(role=role.value)
            .returning(VaultAuthorizationORM)
        )
        result = self._db.execute(stmt)
        updated_orm = result.scalar_one_or_none()
        self._db.commit()
        return self._to_domain(updated_orm) if updated_orm else None

    def get_by_vault_and_user(self, vault_id: str, user_id: str) -> VaultAuthorization | None:
        stmt = select(VaultAuthorizationORM).where(
            VaultAuthorizationORM.vault_id == vault_id,
            VaultAuthorizationORM.user_id == user_id
        )
        orm = self._db.execute(stmt).scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    def list_by_vault(self, vault_id: str) -> list[VaultAuthorization]:
        stmt = select(VaultAuthorizationORM).where(
            VaultAuthorizationORM.vault_id == vault_id
        )
        orms = self._db.execute(stmt).scalars().all()
        return [self._to_domain(orm) for orm in orms]

    def list_by_user(self, user_id: str) -> list[VaultAuthorization]:
        stmt = select(VaultAuthorizationORM).where(
            VaultAuthorizationORM.user_id == user_id
        )
        orms = self._db.execute(stmt).scalars().all()
        return [self._to_domain(orm) for orm in orms]

    def delete(self, vault_id: str, user_id: str) -> None:
        stmt = delete(VaultAuthorizationORM).where(
            VaultAuthorizationORM.vault_id == vault_id,
            VaultAuthorizationORM.user_id == user_id
        )
        self._db.execute(stmt)
        self._db.commit()

    def user_has_access(self, vault_id: str, user_id: str) -> bool:
        stmt = select(VaultAuthorizationORM.id).where(
            VaultAuthorizationORM.vault_id == vault_id,
            VaultAuthorizationORM.user_id == user_id
        )
        result = self._db.execute(stmt).scalar_one_or_none()
        return result is not None

    def get_user_role(self, vault_id: str, user_id: str) -> VaultRole | None:
        stmt = select(VaultAuthorizationORM.role).where(
            VaultAuthorizationORM.vault_id == vault_id,
            VaultAuthorizationORM.user_id == user_id
        )
        role_str = self._db.execute(stmt).scalar_one_or_none()
        return VaultRole(role_str) if role_str else None
