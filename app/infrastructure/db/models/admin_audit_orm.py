"""
Admin audit log ORM model.

Follows AccessLogORM pattern:
- DateTime(timezone=True) for timezone-aware timestamps
- func.now() for server-side default
- JSON (dialect-agnostic, maps to JSONB on PostgreSQL, json on SQLite)
- Index declarations in __table_args__

No admin_user_id column: the internal API authenticates with a shared
X-Admin-Token header, not individual user identities.

Clean Architecture:
    Infrastructure layer — database model only.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base


class AdminAuditORM(Base):
    __tablename__ = "admin_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_audit_created", "created_at"),
        Index("idx_audit_action",  "action"),
    )
