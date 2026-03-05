from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.infrastructure.db.models.face_encoding_orm import FaceEncodingORM


@dataclass(frozen=True)
class DeleteFaceInput:
    user_id: str


@dataclass(frozen=True)
class DeleteFaceResult:
    deleted: bool


class DeleteFace:
    """Delete a user's stored face encoding.

    Returns deleted=False if no encoding exists (idempotent — not an error).
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def execute(self, data: DeleteFaceInput) -> DeleteFaceResult:
        existing = (
            self._db.query(FaceEncodingORM)
            .filter(FaceEncodingORM.user_id == data.user_id)
            .first()
        )
        if not existing:
            return DeleteFaceResult(deleted=False)
        self._db.delete(existing)
        self._db.commit()
        return DeleteFaceResult(deleted=True)
