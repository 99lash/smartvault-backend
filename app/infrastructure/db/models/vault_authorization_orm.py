from __future__ import annotations
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.models.base import Base


class VaultAuthorizationORM(Base):
    __tablename__ = "vault_authorizations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    vault_id: Mapped[str] = mapped_column(ForeignKey("vaults.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    granted_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    vault = relationship("VaultORM", foreign_keys=[vault_id])
    user = relationship("UserORM", foreign_keys=[user_id])
    granter = relationship("UserORM", foreign_keys=[granted_by])

    __table_args__ = (
        UniqueConstraint("vault_id", "user_id", name="uq_vault_user"),
    )
