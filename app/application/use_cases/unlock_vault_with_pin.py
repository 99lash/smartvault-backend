from __future__ import annotations

import time
from dataclasses import dataclass

from app.application.ports.activity_log_repository import ActivityLogRepository
from app.application.ports.pin_attempt_tracker import PINAttemptTracker
from app.application.ports.pin_hasher import PINHasher
from app.application.ports.vault_repository import VaultRepository
from app.application.use_cases.log_activity import LogActivity, LogActivityInput
from app.domain.exceptions import (
    InvalidPINError,
    PINLockedOutError,
    PINNotSetError,
    VaultNotFoundError,
)
from app.domain.models.vault import Vault
from app.domain.value_objects.pin import PIN
from app.domain.value_objects.pin_attempt_result import PINAttemptResult
from app.infrastructure.monitoring.helpers import (
    track_pin_lockout,
    track_vault_unlock,
)


@dataclass(frozen=True)
class UnlockVaultWithPINInput:
    vault_id: str
    pin: str
    user_id: str | None = None  # NEW: who is unlocking


@dataclass(frozen=True)
class UnlockVaultWithPINResult:
    vault: Vault
    result: PINAttemptResult
    attempts_remaining: int | None


class UnlockVaultWithPIN:
    def __init__(
        self,
        repo: VaultRepository,
        hasher: PINHasher,
        tracker: PINAttemptTracker,
        log_activity: LogActivity | None = None,  # NEW: optional, won't break existing tests
    ) -> None:
        self._repo = repo
        self._hasher = hasher
        self._tracker = tracker
        self._log_activity = log_activity

    async def execute(self, inp: UnlockVaultWithPINInput) -> UnlockVaultWithPINResult:
        start = time.perf_counter()
        success = False

        try:
            vault = self._repo.get_by_id(inp.vault_id)
            if vault is None:
                raise VaultNotFoundError(inp.vault_id)

            if vault.pin_hash is None:
                raise PINNotSetError(inp.vault_id)

            if await self._tracker.is_locked_out(inp.vault_id):
                track_pin_lockout()
                self._log(LogActivityInput(
                    vault_id=inp.vault_id,
                    user_id=inp.user_id,
                    action="VAULT_UNLOCK_FAILED",
                    method="PIN",
                    metadata={"reason": "locked_out", "lockout": True},
                ))
                raise PINLockedOutError(inp.vault_id, attempts_remaining=0)

            pin = PIN(inp.pin)

            if not self._hasher.verify(pin, vault.pin_hash):
                result, remaining = await self._tracker.register_failure(inp.vault_id)
                if result is PINAttemptResult.LOCKED_OUT:
                    track_pin_lockout()
                    self._log(LogActivityInput(
                        vault_id=inp.vault_id,
                        user_id=inp.user_id,
                        action="VAULT_UNLOCK_FAILED",
                        method="PIN",
                        metadata={"reason": "max_attempts_reached", "lockout": True},
                    ))
                    raise PINLockedOutError(inp.vault_id, attempts_remaining=0)

                self._log(LogActivityInput(
                    vault_id=inp.vault_id,
                    user_id=inp.user_id,
                    action="VAULT_UNLOCK_FAILED",
                    method="PIN",
                    metadata={
                        "reason": "wrong_pin",
                        "attempts_remaining": remaining,
                        "lockout": False,
                    },
                ))
                message = "Invalid PIN"
                if remaining is not None:
                    message = f"{message}. Attempts remaining: {remaining}"
                raise InvalidPINError(message)

            await self._tracker.register_success(inp.vault_id)
            success = True

            self._log(LogActivityInput(
                vault_id=inp.vault_id,
                user_id=inp.user_id,
                action="VAULT_UNLOCKED",
                method="PIN",
            ))

            return UnlockVaultWithPINResult(
                vault=vault,
                result=PINAttemptResult.SUCCESS,
                attempts_remaining=None,
            )

        finally:
            duration = time.perf_counter() - start
            track_vault_unlock(
                method="pin",
                success=success,
                duration_seconds=duration,
            )

    def _log(self, inp: LogActivityInput) -> None:
        """Fire-and-forget activity logging. Never raises."""
        if self._log_activity is None:
            return
        try:
            self._log_activity.execute(inp)
        except Exception:
            pass