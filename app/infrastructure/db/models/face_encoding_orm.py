from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base


class FaceEncodingORM(Base):
    """Stores the 128-dimensional face encoding for a user.

    Only one encoding per user (unique constraint on user_id).
    Re-enrollment overwrites the existing row.
    Raw images are never persisted — only numerical vectors.
    """

    __tablename__ = "face_encodings"
    __table_args__ = (UniqueConstraint("user_id", name="uq_face_encodings_user_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    encoding: Mapped[str] = mapped_column(Text, nullable=False)  # JSON list[float], 128 dims
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
