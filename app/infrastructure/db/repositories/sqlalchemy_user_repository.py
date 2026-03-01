from __future__ import annotations
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import select, update

from app.application.ports.user_repository import UserRepository
from app.application.use_cases.create_user import DuplicateEmailError
from app.domain.models.user import User
from app.infrastructure.db.models.user_orm import UserORM

class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, db: Session):
        self._db = db  # We use self._db consistently now

    # Helper method that was missing
    def _to_domain(self, orm: UserORM) -> User:
        return User(
            id=orm.id,
            email=orm.email,
            password_hash=orm.password_hash,
            full_name=orm.full_name,
            created_at=orm.created_at,
            provisioning_token=orm.provisioning_token,
        )

    def save(self, user: User) -> None:
        orm = UserORM(
            id=user.id,
            email=user.email,
            password_hash=user.password_hash,
            full_name=user.full_name,
            created_at=user.created_at,
            provisioning_token=user.provisioning_token,
        )
        self._db.merge(orm)  # FIXED: uses self._db
        self._db.flush()     # FIXED: uses self._db
        
    def get_by_email(self, email: str) -> User | None:
        row = (
            self._db.query(UserORM)
            .filter(UserORM.email == email.strip().lower())
            .one_or_none()
        )
        if row is None:
            return None
        return self._to_domain(row) # Cleanup: use helper

    def create(self, user: User) -> User:
        row = UserORM(
            id=user.id,
            email=user.email,
            password_hash=user.password_hash,
            full_name=getattr(user, "full_name", None),
            created_at=user.created_at, # Ensure created_at is passed if needed
            provisioning_token=getattr(user, "provisioning_token", None),
        )
        self._db.add(row)
        try:
            self._db.commit()
        except IntegrityError as e:
            self._db.rollback()
            raise DuplicateEmailError(user.email) from e

        self._db.refresh(row)
        return self._to_domain(row) # Cleanup: use helper

    def get_by_id(self, user_id: str) -> User | None:
        stmt = select(UserORM).where(UserORM.id == user_id)
        orm = self._db.execute(stmt).scalar_one_or_none() # FIXED: uses self._db
        return self._to_domain(orm) if orm else None

    def get_by_ids(self, user_ids: list[str]) -> dict[str, User]:
        if not user_ids:
            return {}
        stmt = select(UserORM).where(UserORM.id.in_(user_ids))
        orms = self._db.execute(stmt).scalars().all()
        return {orm.id: self._to_domain(orm) for orm in orms}

    def update_profile(self, user_id: str, full_name: str | None) -> User | None:
        stmt = (
            update(UserORM)
            .where(UserORM.id == user_id)
            .values(full_name=full_name)
            .returning(UserORM)
        )
        result = self._db.execute(stmt) # FIXED: uses self._db
        updated_orm = result.scalar_one_or_none()
        self._db.flush()                # FIXED: uses self._db
        return self._to_domain(updated_orm) if updated_orm else None

    def update_password(self, user_id: str, password_hash: str) -> User | None:
        stmt = (
            update(UserORM)
            .where(UserORM.id == user_id)
            .values(password_hash=password_hash)
            .returning(UserORM)
        )
        result = self._db.execute(stmt)
        updated_orm = result.scalar_one_or_none()
        self._db.flush()
        return self._to_domain(updated_orm) if updated_orm else None

    def get_by_provisioning_token(self, token: str) -> User | None:
        row = (
            self._db.query(UserORM)
            .filter(UserORM.provisioning_token == token)
            .one_or_none()
        )
        if row is None:
            return None
        return self._to_domain(row)

    def set_provisioning_token(self, user_id: str, token: str) -> None:
        row = self._db.get(UserORM, user_id)
        if row is None:
            raise ValueError(f"User {user_id} not found")
        row.provisioning_token = token
        self._db.commit()

    def clear_provisioning_token(self, user_id: str) -> None:
        row = self._db.get(UserORM, user_id)
        if row is None:
            raise ValueError(f"User {user_id} not found")
        row.provisioning_token = None
        self._db.commit()
