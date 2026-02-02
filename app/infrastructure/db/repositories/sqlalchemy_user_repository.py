from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.ports.user_repository import UserRepository
from app.application.use_cases.create_user import DuplicateEmailError
from app.domain.models.user import User
from app.infrastructure.db.models.user_orm import UserORM


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, db: Session):
        self._db = db

    def get_by_email(self, email: str) -> User | None:
        row = (
            self._db.query(UserORM)
            .filter(UserORM.email == email.strip().lower())
            .one_or_none()
        )
        if row is None:
            return None
        return User(
            id=row.id,
            email=row.email,
            password_hash=row.password_hash,
            full_name=row.full_name,
            created_at=row.created_at,
        )

    def create(self, user: User) -> User:
        row = UserORM(
            id=user.id,
            email=user.email,
            password_hash=user.password_hash,
            full_name=getattr(user, "full_name", None),
        )
        self._db.add(row)
        try:
            self._db.commit()
        except IntegrityError as e:
            self._db.rollback()
            # DB is the final guard for uniqueness
            raise DuplicateEmailError(user.email) from e

        self._db.refresh(row)
        return User(
            id=row.id,
            email=row.email,
            password_hash=row.password_hash,
            full_name=row.full_name,
            created_at=row.created_at,
        )
