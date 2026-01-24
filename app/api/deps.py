import os

from fastapi import Depends
from sqlalchemy.orm import Session

from app.application.ports.vault_repository import VaultRepository
from app.infrastructure.db.repositories.in_memory_vault_repository import InMemoryVaultRepository
from app.infrastructure.db.repositories.sqlalchemy_vault_repository import SqlAlchemyVaultRepository
from app.infrastructure.db.session import get_db


_in_memory_repo = InMemoryVaultRepository()


def _running_pytest() -> bool:
    return "PYTEST_CURRENT_TEST" in os.environ


def get_vault_repo(db: Session = Depends(get_db)) -> VaultRepository:
    # Tests/CI: do NOT touch the database.
    if _running_pytest():
        return _in_memory_repo

    # Normal runs: use Postgres via SQLAlchemy.
    return SqlAlchemyVaultRepository(db)


def get_current_user_id() -> str:
    return "demo-user-1"
