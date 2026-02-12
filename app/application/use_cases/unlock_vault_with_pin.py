from __future__ import annotations

import time  # ← FIXED: added missing import
from dataclasses import dataclass

from app.application.ports.pin_attempt_tracker import PINAttemptTracker
from app.application.ports.pin_hasher import PINHasher
from app.application.ports.vault_repository import VaultRepository
from app.domain.exceptions import (
    InvalidPINError,
    PINLockedOutError,
    PINNotSetError,
    VaultNotFoundError,
)
from app.domain.models.vault import Vault
from app.domain.value_objects.pin import PIN
from app.domain.value_objects.pin_attempt_result import PINAttemptResult

# Metrics import
from app.infrastructure.monitoring.helpers import (
    track_vault_unlock,
    track_pin_lockout,
)


@dataclass(frozen=True)
class UnlockVaultWithPINInput:
    vault_id: str
    pin: str


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
    ) -> None:
        self._repo = repo
        self._hasher = hasher
        self._tracker = tracker

    async def execute(self, inp: UnlockVaultWithPINInput) -> UnlockVaultWithPINResult:
        # Track duration and success/failure of vault unlock attempts (business metric)
        start = time.perf_counter()
        success = False

        try:  # ← FIXED: wraps all business logic so finally always runs
            vault = self._repo.get_by_id(inp.vault_id)
            if vault is None:
                raise VaultNotFoundError(inp.vault_id)

            if vault.pin_hash is None:
                raise PINNotSetError(inp.vault_id)

            # Check lockout before verifying
            if await self._tracker.is_locked_out(inp.vault_id):
                # Track lockout event (security metric)
                track_pin_lockout()
                raise PINLockedOutError(inp.vault_id, attempts_remaining=0)

            pin = PIN(inp.pin)  # validates format/weak patterns

            if not self._hasher.verify(pin, vault.pin_hash):
                result, remaining = await self._tracker.register_failure(inp.vault_id)
                if result is PINAttemptResult.LOCKED_OUT:
                    # Track lockout event on threshold breach
                    track_pin_lockout()
                    raise PINLockedOutError(inp.vault_id, attempts_remaining=0)
                message = "Invalid PIN"
                if remaining is not None:
                    message = f"{message}. Attempts remaining: {remaining}"
                raise InvalidPINError(message)

            # Success path
            await self._tracker.register_success(inp.vault_id)

            # Mark as successful before returning
            success = True

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