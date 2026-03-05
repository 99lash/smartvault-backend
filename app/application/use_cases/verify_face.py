from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.infrastructure.biometrics.face_recognition_service import FaceRecognitionService
from app.infrastructure.db.models.face_encoding_orm import FaceEncodingORM


class FaceNotEnrolledError(Exception):
    """Raised when the user has no stored face encoding."""


class FaceVerificationFailedError(Exception):
    """Raised when the live face does not match the stored encoding."""


@dataclass(frozen=True)
class VerifyFaceInput:
    user_id: str
    image_bytes: bytes


@dataclass(frozen=True)
class VerifyFaceResult:
    success: bool


class VerifyFace:
    """Verify a live photo against a stored face encoding.

    This use case only handles face recognition — vault unlock logic
    lives in the endpoint so async operations (WebSocket) remain there.

    Raises:
        FaceNotEnrolledError: User has no stored encoding.
        FaceVerificationFailedError: Live photo does not match stored encoding.
        ValueError: No face detected in the provided image.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def execute(self, data: VerifyFaceInput) -> VerifyFaceResult:
        stored = (
            self._db.query(FaceEncodingORM)
            .filter(FaceEncodingORM.user_id == data.user_id)
            .first()
        )
        if not stored:
            raise FaceNotEnrolledError(f"No face encoding found for user {data.user_id}")

        live_encoding = FaceRecognitionService.encode(data.image_bytes)  # raises ValueError if no face
        if not FaceRecognitionService.match(stored.encoding, live_encoding):
            raise FaceVerificationFailedError("Face does not match stored encoding")

        return VerifyFaceResult(success=True)
