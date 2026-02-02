from fastapi import Depends
from sqlalchemy.orm import Session

from app.application.ports.vault_repository import VaultRepository
from app.infrastructure.db.repositories.sqlalchemy_vault_repository import SqlAlchemyVaultRepository
from app.infrastructure.db.session import get_db


def get_vault_repo(db: Session = Depends(get_db)) -> VaultRepository:
    return SqlAlchemyVaultRepository(db)


def get_current_user_id() -> str:
    return "demo-user-1"