from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

# All valid action types for an access log entry.
# Using Literal keeps this in pure Python — no DB enum, no import overhead.
ActivityAction = Literal[
    "VAULT_UNLOCKED",
    "VAULT_UNLOCK_FAILED",
    "VAULT_STATE_CHANGED",
    "VAULT_RESET",
    "UNLOCK_COMMAND_SENT",
    "PIN_SET",
    "MEMBER_ADDED",
    "MEMBER_REMOVED",
    "TAMPER_DETECTED",
]

# All valid method types describing how the action was triggered.
ActivityMethod = Literal[
    "PIN",
    "BIOMETRIC",
    "COMMAND",
    "SYSTEM",
]


@dataclass(frozen=True)
class AccessLog:
    id: str
    vault_id: str
    user_id: str | None
    action: ActivityAction
    method: ActivityMethod
    metadata: dict | None
    created_at: datetime
