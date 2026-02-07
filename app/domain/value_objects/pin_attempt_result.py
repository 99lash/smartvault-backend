from enum import Enum


class PINAttemptResult(str, Enum):
    SUCCESS = "SUCCESS"
    INVALID = "INVALID"
    LOCKED_OUT = "LOCKED_OUT"

    def is_success(self) -> bool:
        return self is PINAttemptResult.SUCCESS

