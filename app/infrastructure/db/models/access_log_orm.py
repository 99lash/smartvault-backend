from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base


class AccessLogORM(Base):
    __tablename__ = "access_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    vault_id: Mapped[str] = mapped_column(
        ForeignKey("vaults.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    # JSON is dialect-agnostic: maps to jsonb on PostgreSQL, json on SQLite.
    # The migration explicitly uses JSONB — this model stays portable for tests.
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_access_logs_vault_created", "vault_id", "created_at"),
        Index("ix_access_logs_user_created", "user_id", "created_at"),
    )