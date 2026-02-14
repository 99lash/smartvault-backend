from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.application.ports.pin_hasher import PINHasher
from app.application.ports.vault_repository import VaultRepository
from app.application.use_cases.log_activity import LogActivity, LogActivityInput
from app.domain.exceptions import VaultNotFoundError
from app.domain.models.vault import Vault
from app.domain.value_objects.pin import PIN
from app.infrastructure.monitoring.helpers import track_vault_pin_set


@dataclass(frozen=True)
class SetVaultPINInput:
    vault_id: str
    pin: str
    user_id: str | None = None  


@dataclass(frozen=True)
class SetVaultPINResult:
    vault: Vault


class SetVaultPIN:
    def __init__(
        self,
        repo: VaultRepository,
        hasher: PINHasher,
        log_activity: LogActivity | None = None,  
    ) -> None:
        self._repo = repo
        self._hasher = hasher
        self._log_activity = log_activity

    def execute(self, inp: SetVaultPINInput) -> SetVaultPINResult:
        vault = self._repo.get_by_id(inp.vault_id)
        if vault is None:
            raise VaultNotFoundError(inp.vault_id)

        pin = PIN(inp.pin)
        hashed = self._hasher.hash(pin)
        now = datetime.now(timezone.utc)

        updated_vault = self._repo.update_pin(vault.id, hashed, now)

        track_vault_pin_set()

        if self._log_activity:
            try:
                self._log_activity.execute(LogActivityInput(
                    vault_id=inp.vault_id,
                    user_id=inp.user_id,
                    action="PIN_SET",
                    method="SYSTEM",
                ))
            except Exception:
                pass

        return SetVaultPINResult(vault=updated_vault)