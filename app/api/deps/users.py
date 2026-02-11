from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps.common import get_current_user_id, get_db_session
from app.application.ports.user_repository import UserRepository
from app.application.services.password_hasher_service import PBKDF2PasswordHasher
from app.application.use_cases.create_user import CreateUser
from app.application.use_cases.authenticate_user import AuthenticateUser
from app.application.use_cases.get_me import GetMe
from app.application.use_cases.update_me import UpdateMe
from app.infrastructure.db.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.domain.models.user import User

_password_hasher = PBKDF2PasswordHasher()


def get_user_repo(db: Session = Depends(get_db_session)) -> UserRepository:
    """Get user repository."""
    return SqlAlchemyUserRepository(db)


def get_password_hasher() -> PBKDF2PasswordHasher:
    return _password_hasher


def get_create_user_uc(
    repo: UserRepository = Depends(get_user_repo),
    hasher: PBKDF2PasswordHasher = Depends(get_password_hasher),
) -> CreateUser:
    return CreateUser(repo=repo, hasher=hasher)  # TODO: Protocol later

def get_authenticate_user_uc(
    repo: UserRepository = Depends(get_user_repo),
    hasher: PBKDF2PasswordHasher = Depends(get_password_hasher),
) -> AuthenticateUser:
    return AuthenticateUser(repo=repo, hasher=hasher)

def get_get_me_uc(repo: UserRepository = Depends(get_user_repo)) -> GetMe:
    return GetMe(repo)

def get_update_me_uc(repo: UserRepository = Depends(get_user_repo)) -> UpdateMe:
    return UpdateMe(repo)

def get_current_user(
    repo: UserRepository = Depends(get_user_repo),
    user_id: str = Depends(get_current_user_id),
) -> User:
    user = repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user
