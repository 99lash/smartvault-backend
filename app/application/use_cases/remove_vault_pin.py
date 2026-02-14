from __future__ import annotations

from dataclasses import dataclass, replace

from app.application.ports.vault_repository import VaultRepository
from app.application.use_cases.log_activity import LogActivity, LogActivityInput
from app.domain.exceptions import PINNotSetError, VaultNotFoundError
from app.domain.models.vault import Vault


@dataclass(frozen=True)
class RemoveVaultPINInput:
    vault_id: str
    user_id: str | None = None  


@dataclass(frozen=True)
class RemoveVaultPINResult:
    vault: Vault


class RemoveVaultPIN:
    def __init__(
        self,
        repo: VaultRepository,
        log_activity: LogActivity | None = None,  
    ) -> None:
        self._repo = repo
        self._log_activity = log_activity

    def execute(self, inp: RemoveVaultPINInput) -> RemoveVaultPINResult:
        vault = self._repo.get_by_id(inp.vault_id)
        if vault is None:
            raise VaultNotFoundError(inp.vault_id)

        if vault.pin_hash is None:
            raise PINNotSetError(inp.vault_id)

        updated = replace(vault, pin_hash=None, pin_set_at=None)
        saved = self._repo.update(updated)

        if self._log_activity:
            try:
                self._log_activity.execute(LogActivityInput(
                    vault_id=inp.vault_id,
                    user_id=inp.user_id,
                    action="PIN_SET",
                    method="SYSTEM",
                    metadata={"operation": "removed"},
                ))
            except Exception:
                pass

        return RemoveVaultPINResult(vault=saved)