from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from app.domain.exceptions import InvalidPINError


@dataclass(frozen=True, slots=True)
class PIN:
    """
    Immutable value object representing a vault PIN.

    Business rules:
    - Exactly 6 characters long.
    - Numeric digits only.
    - Reject weak patterns (identical digits, sequential, or repeated substrings).
    """

    value: str

    LENGTH: ClassVar[int] = 6

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        object.__setattr__(self, "value", normalized)
        self._validate(normalized)

    @classmethod
    def _validate(cls, pin: str) -> None:
        if len(pin) != cls.LENGTH:
            raise InvalidPINError("PIN must be exactly 6 digits.")
        if not pin.isdigit():
            raise InvalidPINError("PIN must contain only numeric digits.")
        if cls._is_weak(pin):
            raise InvalidPINError("PIN pattern is too weak.")

    @classmethod
    def _is_weak(cls, pin: str) -> bool:
        # All digits identical (e.g., 000000)
        if len(set(pin)) == 1:
            return True

        # Strictly ascending or descending sequences (e.g., 123456, 987654)
        if cls._is_sequential(pin, step=1) or cls._is_sequential(pin, step=-1):
            return True

        # Repeated substrings (e.g., 121212, 123123)
        for segment_size in (2, 3):
            segment = pin[:segment_size]
            if segment * (cls.LENGTH // segment_size) == pin:
                return True

        return False

    @staticmethod
    def _is_sequential(pin: str, *, step: int) -> bool:
        digits = [int(char) for char in pin]
        return all((digits[i] - digits[i - 1]) == step for i in range(1, len(digits)))

    def __str__(self) -> str:  # pragma: no cover - convenience
        return self.value

