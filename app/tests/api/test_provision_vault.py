from fastapi.testclient import TestClient

from app.api.deps import get_vault_repo
from app.infrastructure.db.repositories.in_memory_vault_repository import (
    InMemoryVaultRepository,
)
from app.main import app


def _client_with_fresh_repo() -> TestClient:
    repo = InMemoryVaultRepository()
    app.dependency_overrides[get_vault_repo] = lambda: repo
    return TestClient(app)


def test_provision_vault_success() -> None:
    client = _client_with_fresh_repo()
    payload = {"hardware_uuid": "ESP32-ABC-123", "nickname": "Bedroom Vault"}

    try:
        response = client.post("/api/v1/vaults/provision", json=payload)

        assert response.status_code == 201
        body = response.json()
        assert isinstance(body["vault_id"], str)
        assert body["vault_id"].startswith("vault_")
        assert body["hardware_uuid"] == payload["hardware_uuid"]
        assert body["nickname"] == payload["nickname"]
        assert body["status"] == "LOCKED"
    finally:
        app.dependency_overrides.clear()


def test_provision_vault_conflict() -> None:
    client = _client_with_fresh_repo()
    payload = {"hardware_uuid": "ESP32-DUPE-001", "nickname": None}

    try:
        first = client.post("/api/v1/vaults/provision", json=payload)
        assert first.status_code == 201

        second = client.post("/api/v1/vaults/provision", json=payload)
        assert second.status_code == 409
        assert second.json()["detail"] == "Hardware already provisioned"
    finally:
        app.dependency_overrides.clear()
