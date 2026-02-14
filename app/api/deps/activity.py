from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.deps.common import get_db_session
from app.application.ports.activity_log_repository import ActivityLogRepository
from app.application.use_cases.log_activity import LogActivity
from app.infrastructure.db.repositories.sqlalchemy_activity_log_repository import (
    SqlAlchemyActivityLogRepository,
)


def get_activity_log_repo(
    db: Session = Depends(get_db_session),
) -> ActivityLogRepository:
    """Provide a SQLAlchemy-backed ActivityLogRepository."""
    return SqlAlchemyActivityLogRepository(db)


def get_log_activity_uc(
    repo: ActivityLogRepository = Depends(get_activity_log_repo),
) -> LogActivity:        
    """Provide a ready-to-use LogActivity use case."""
    return LogActivity(repo)