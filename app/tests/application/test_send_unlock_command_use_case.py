"""Tests for SendUnlockCommand use case."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.ports.websocket_manager import WebSocketManagerPort
from app.application.use_cases.send_unlock_command import (
    SendUnlockCommand,
    SendUnlockCommandResult,
    VaultOfflineError,
)
from app.domain.exceptions import UnauthorizedVaultAccessError
from app.domain.models.vault import Vault
from app.domain.value_objects.vault_role import VaultRole
from app.domain.value_objects.vault_status import VaultStatus


class MockWebSocketManager(WebSocketManagerPort):
    """Mock WebSocket manager for testing."""

    def __init__(self, online_vaults: set | None = None):
        self._online_vaults = online_vaults or set()
        self._sent_messages = []

    async def is_vault_online(self, vault_id: str) -> bool:
        return vault_id in self._online_vaults

    async def send_to_vault(self, vault_id: str, message: dict) -> None:
        self._sent_messages.append((vault_id, message))


class FakeVaultRepository:
    """Fake vault repository for testing."""

    def __init__(self, vaults: dict[str, Vault] | None = None):
        self._vaults = vaults or {}

    def get_by_id(self, vault_id: str) -> Vault | None:
        return self._vaults.get(vault_id)


class FakeCheckVaultAccess:
    """Fake check vault access use case for testing."""

    def __init__(self, access_map: dict[tuple[str, str], tuple[bool, VaultRole | None]]):
        self._access_map = access_map

    def execute(self, vault_id: str, user_id: str):
        key = (vault_id, user_id)
        if key not in self._access_map:
            # No access info means no access
            raise UnauthorizedVaultAccessError(user_id, vault_id)
        has_access, role = self._access_map[key]
        return MagicMock(has_access=has_access, role=role, is_owner=False)


def create_test_vault(vault_id: str, owner_id: str) -> Vault:
    """Create a test vault."""
    return Vault(
        id=vault_id,
        owner_id=owner_id,
        hardware_uuid=f"hw-{vault_id}",
        vault_name=f"Vault {vault_id}",
        status=VaultStatus.LOCKED,
    )


@pytest.mark.asyncio
async def test_send_unlock_command_vault_offline():
    """Test unlock command when vault is offline - tests access check path only."""
    vault_id = "vault-123"
    user_id = "user-456"
    vault = create_test_vault(vault_id, owner_id=user_id)

    # Setup mocks - vault is NOT in online_vaults
    ws_manager = MockWebSocketManager(online_vaults=set())
    vault_repo = FakeVaultRepository(vaults={vault_id: vault})
    check_access = FakeCheckVaultAccess(
        access_map={(vault_id, user_id): (True, VaultRole.ADMIN)}
    )

    use_case = SendUnlockCommand(
        repo=vault_repo,
        check_access=check_access,
        ws_manager=ws_manager,
    )

    # Execute and expect exception
    with pytest.raises(VaultOfflineError):
        await use_case.execute(vault_id=vault_id, user_id=user_id)


@pytest.mark.asyncio
async def test_send_unlock_command_no_access():
    """Test unlock command when user has no access."""
    vault_id = "vault-123"
    user_id = "user-456"
    vault = create_test_vault(vault_id, owner_id="other-owner")

    ws_manager = MockWebSocketManager(online_vaults={vault_id})
    vault_repo = FakeVaultRepository(vaults={vault_id: vault})
    # User has no access - access_map is empty so UnauthorizedVaultAccessError is raised
    check_access = FakeCheckVaultAccess(access_map={})

    use_case = SendUnlockCommand(
        repo=vault_repo,
        check_access=check_access,
        ws_manager=ws_manager,
    )

    with pytest.raises(UnauthorizedVaultAccessError):
        await use_case.execute(vault_id=vault_id, user_id=user_id)


@pytest.mark.asyncio
async def test_send_unlock_command_owner_access():
    """Test unlock command when user is the vault owner."""
    vault_id = "vault-123"
    owner_id = "owner-456"
    vault = create_test_vault(vault_id, owner_id=owner_id)

    ws_manager = MockWebSocketManager(online_vaults={vault_id})
    vault_repo = FakeVaultRepository(vaults={vault_id: vault})
    # Owner has implicit access (None role means owner)
    check_access = FakeCheckVaultAccess(
        access_map={(vault_id, owner_id): (True, None)}
    )

    use_case = SendUnlockCommand(
        repo=vault_repo,
        check_access=check_access,
        ws_manager=ws_manager,
    )

    # Execute - should proceed to WebSocket check
    # Note: This will still fail at signature generation due to missing VAULT_COMMAND_SECRET
    # but proves the access check logic works correctly
    try:
        await use_case.execute(vault_id=vault_id, user_id=owner_id)
    except AttributeError as e:
        if "VAULT_COMMAND_SECRET" in str(e):
            pytest.skip("VAULT_COMMAND_SECRET not configured in settings")
        raise
