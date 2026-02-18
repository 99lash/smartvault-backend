from dataclasses import replace
from datetime import datetime, timezone

from app.domain.models.vault_authorization import VaultAuthorization
from app.domain.value_objects.vault_role import VaultRole


def _set_vault_owner(vault_repo, vault_id: str, owner_id: str) -> None:
    vault = vault_repo._vaults[vault_id]
    vault_repo._vaults[vault_id] = replace(vault, owner_id=owner_id)


def test_list_vaults_returns_owned_vaults(client, vault_repo):
    _set_vault_owner(vault_repo, "demo-vault-1", "test-user-id")
    _set_vault_owner(vault_repo, "demo-vault-2", "test-user-id")

    response = client.get("/api/v1/vaults")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2

    ids = {item["vault_id"] for item in data}
    assert "demo-vault-1" in ids

    item = next(item for item in data if item["vault_id"] == "demo-vault-1")
    assert item["role"] == "OWNER"
    assert item["name"] == "Demo Vault 1"


def test_list_vaults_includes_member_vaults(client, vault_repo, vault_auth_repo):
    _set_vault_owner(vault_repo, "demo-vault-1", "someone-else")
    _set_vault_owner(vault_repo, "demo-vault-2", "someone-else")

    vault_auth_repo.create(
        VaultAuthorization(
            id="auth-1",
            vault_id="demo-vault-1",
            user_id="test-user-id",
            role=VaultRole.MEMBER,
            granted_by="owner-1",
            granted_at=datetime.now(timezone.utc),
        )
    )

    response = client.get("/api/v1/vaults")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["vault_id"] == "demo-vault-1"
    assert data[0]["role"] == "MEMBER"


def test_list_vaults_empty_when_no_access(client):
    response = client.get("/api/v1/vaults")

    assert response.status_code == 200
    assert response.json() == []
