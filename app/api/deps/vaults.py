from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.deps.common import get_db_session, running_pytest
from app.application.ports.vault_repository import VaultRepository
from app.infrastructure.db.repositories.in_memory_vault_repository import InMemoryVaultRepository
from app.infrastructure.db.repositories.sqlalchemy_vault_repository import SqlAlchemyVaultRepository

_in_memory_vault_repo = InMemoryVaultRepository()


def get_vault_repo(db: Session = Depends(get_db_session)) -> VaultRepository:
    if running_pytest():
        return _in_memory_vault_repo
    return SqlAlchemyVaultRepository(db)


def get_current_user_id() -> str:
    return "demo-user-1"
