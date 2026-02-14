from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.application.ports.activity_log_repository import ActivityLogRepository
from app.domain.models.access_log import AccessLog, ActivityAction, ActivityMethod
from app.infrastructure.db.models.access_log_orm import AccessLogORM


class SqlAlchemyActivityLogRepository(ActivityLogRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    # -------------------------------------------------------------------------
    # Private mapper
    # -------------------------------------------------------------------------

    def _to_domain(self, row: AccessLogORM) -> AccessLog:
        return AccessLog(
            id=row.id,
            vault_id=row.vault_id,
            user_id=row.user_id,
            action=row.action,       # type: ignore[arg-type]
            method=row.method,       # type: ignore[arg-type]
            metadata=row.metadata_,
            created_at=row.created_at,
        )

    # -------------------------------------------------------------------------
    # Port implementation
    # -------------------------------------------------------------------------

    def create(self, log: AccessLog) -> AccessLog:
        row = AccessLogORM(
            id=log.id,
            vault_id=log.vault_id,
            user_id=log.user_id,
            action=log.action,
            method=log.method,
            metadata_=log.metadata,
            created_at=log.created_at,
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return self._to_domain(row)

    def list_by_vault(
        self,
        vault_id: str,
        *,
        limit: int = 50,
        before: datetime | None = None,
    ) -> list[AccessLog]:
        stmt = (
            select(AccessLogORM)
            .where(AccessLogORM.vault_id == vault_id)
            .order_by(AccessLogORM.created_at.desc())
            .limit(min(limit, 100))   # hard cap at 100 to avoid runaway queries
        )

        if before is not None:
            stmt = stmt.where(AccessLogORM.created_at < before)

        rows = self._session.execute(stmt).scalars().all()
        return [self._to_domain(row) for row in rows]

    def count_recent_by_action(
        self,
        action: str,
        *,
        since: datetime,
    ) -> int:
        result = self._session.scalar(
            select(func.count())
            .select_from(AccessLogORM)
            .where(AccessLogORM.action == action)
            .where(AccessLogORM.created_at >= since)
        )
        return result or 0