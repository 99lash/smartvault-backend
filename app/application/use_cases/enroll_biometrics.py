from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.infrastructure.db.models.biometric_enrollment_orm import BiometricEnrollmentORM


@dataclass(frozen=True)
class EnrollBiometricsInput:
    user_id: str


@dataclass(frozen=True)
class EnrollBiometricsResult:
    enrolled: bool
    enrolled_at: datetime


class EnrollBiometrics:
    """Record or refresh a user's biometric enrollment.

    Upsert semantics: if the user already has an enrollment row, update
    enrolled_at; otherwise insert a new row.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def execute(self, data: EnrollBiometricsInput) -> EnrollBiometricsResult:
        existing = (
            self._db.query(BiometricEnrollmentORM)
            .filter(BiometricEnrollmentORM.user_id == data.user_id)
            .first()
        )

        now = datetime.now(timezone.utc)

        if existing:
            existing.enrolled_at = now  # type: ignore[assignment]
            self._db.commit()
            return EnrollBiometricsResult(enrolled=True, enrolled_at=now)

        record = BiometricEnrollmentORM(
            id=str(uuid.uuid4()),
            user_id=data.user_id,
            enrolled_at=now,
            last_used_at=None,
        )
        self._db.add(record)
        self._db.commit()
        return EnrollBiometricsResult(enrolled=True, enrolled_at=now)
