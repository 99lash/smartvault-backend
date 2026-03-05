from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.biometrics.face_recognition_service import FaceRecognitionService
from app.infrastructure.db.models.face_encoding_orm import FaceEncodingORM


@dataclass(frozen=True)
class EnrollFaceInput:
    user_id: str
    image_bytes: bytes


@dataclass(frozen=True)
class EnrollFaceResult:
    enrolled: bool


class EnrollFace:
    """Encode and store (or update) a user's face encoding.

    Upsert semantics: if the user already has an encoding, it is replaced.
    Raw images are never persisted — only the 128-d numerical vector.

    Raises:
        ValueError: If no face is detected in the provided image.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def execute(self, data: EnrollFaceInput) -> EnrollFaceResult:
        encoding = FaceRecognitionService.encode(data.image_bytes)  # raises ValueError if no face
        encoding_json = json.dumps(encoding)
        now = datetime.now(timezone.utc)

        existing = (
            self._db.query(FaceEncodingORM)
            .filter(FaceEncodingORM.user_id == data.user_id)
            .first()
        )

        if existing:
            existing.encoding = encoding_json  # type: ignore[assignment]
            existing.updated_at = now  # type: ignore[assignment]
        else:
            self._db.add(FaceEncodingORM(
                id=str(uuid.uuid4()),
                user_id=data.user_id,
                encoding=encoding_json,
                created_at=now,
                updated_at=now,
            ))

        self._db.commit()
        return EnrollFaceResult(enrolled=True)
