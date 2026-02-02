import os

from fastapi import Depends
from sqlalchemy.orm import Session

from app.infrastructure.db.session import get_db

from app.application.ports.vault_repository import VaultRepository
from app.infrastructure.db.repositories.in_memory_vault_repository import InMemoryVaultRepository
from app.infrastructure.db.repositories.sqlalchemy_vault_repository import SqlAlchemyVaultRepository

# ----- vault deps -----
_in_memory_vault_repo = InMemoryVaultRepository()


def _running_pytest() -> bool:
    return "PYTEST_CURRENT_TEST" in os.environ


def get_vault_repo(db: Session = Depends(get_db)) -> VaultRepository:
    # Tests/CI: do NOT touch the database.
    if _running_pytest():
        return _in_memory_vault_repo

    # Normal runs: use Postgres via SQLAlchemy.
    return SqlAlchemyVaultRepository(db)


def get_current_user_id() -> str:
    return "demo-user-1"


# ----- user deps -----
from app.application.ports.user_repository import UserRepository
from app.application.use_cases.create_user import CreateUser
from app.application.services.password_hasher_service import PBKDF2PasswordHasher
from app.infrastructure.db.repositories.in_memory_user_repository import InMemoryUserRepository
from app.infrastructure.db.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository

_in_memory_user_repo = InMemoryUserRepository()
_password_hasher = PBKDF2PasswordHasher()


def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    if _running_pytest():
        return _in_memory_user_repo
    return SqlAlchemyUserRepository(db)


def get_password_hasher() -> PBKDF2PasswordHasher:
    return _password_hasher


def get_create_user_uc(
    repo: UserRepository = Depends(get_user_repo),
    hasher: PBKDF2PasswordHasher = Depends(get_password_hasher),
) -> CreateUser:
    return CreateUser(repo=repo, hasher=hasher)
