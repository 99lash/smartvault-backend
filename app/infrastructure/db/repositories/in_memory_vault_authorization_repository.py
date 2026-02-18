from __future__ import annotations
from typing import Optional

from app.application.ports.vault_authorization_repository import VaultAuthorizationRepository
from app.domain.models.vault_authorization import VaultAuthorization
from app.domain.value_objects.vault_role import VaultRole


class InMemoryVaultAuthorizationRepository(VaultAuthorizationRepository):
    """In-memory implementation for testing."""

    def __init__(self):
        self._store: dict[tuple[str, str], VaultAuthorization] = {}  # key: (vault_id, user_id)

    def create(self, auth: VaultAuthorization) -> VaultAuthorization:
        key = (auth.vault_id, auth.user_id)
        self._store[key] = auth
        return auth

    def update_role(self, vault_id: str, user_id: str, role: VaultRole) -> VaultAuthorization | None:
        key = (vault_id, user_id)
        if key not in self._store:
            return None

        old_auth = self._store[key]
        updated_auth = VaultAuthorization(
            id=old_auth.id,
            vault_id=old_auth.vault_id,
            user_id=old_auth.user_id,
            role=role,
            granted_by=old_auth.granted_by,
            granted_at=old_auth.granted_at,
        )
        self._store[key] = updated_auth
        return updated_auth

    def get_by_vault_and_user(self, vault_id: str, user_id: str) -> Optional[VaultAuthorization]:
        return self._store.get((vault_id, user_id))

    def list_by_vault(self, vault_id: str) -> list[VaultAuthorization]:
        return [auth for (v_id, _), auth in self._store.items() if v_id == vault_id]

    def list_by_user(self, user_id: str) -> list[VaultAuthorization]:
        return [auth for (_, u_id), auth in self._store.items() if u_id == user_id]

    def delete(self, vault_id: str, user_id: str) -> None:
        key = (vault_id, user_id)
        self._store.pop(key, None)

    def user_has_access(self, vault_id: str, user_id: str) -> bool:
        return (vault_id, user_id) in self._store

    def get_user_role(self, vault_id: str, user_id: str) -> VaultRole | None:
        auth = self.get_by_vault_and_user(vault_id, user_id)
        return auth.role if auth else None

    def clear(self) -> None:
        """Test helper to clear all data."""
        self._store.clear()
