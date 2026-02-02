from fastapi.testclient import TestClient


def test_provision_vault_success(client: TestClient) -> None:
    payload = {"hardware_uuid": "ESP32-ABC-123", "vault_name": "Bedroom Vault"}

    response = client.post("/api/v1/vaults/provision", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["vault_id"], str)
    assert body["vault_id"].startswith("vault_")
    assert body["hardware_uuid"] == payload["hardware_uuid"]
    assert body["vault_name"] == payload["vault_name"]
    assert body["status"] == "LOCKED"


def test_provision_vault_conflict(client: TestClient) -> None:
    payload = {"hardware_uuid": "ESP32-DUPE-001", "vault_name": None}

    first = client.post("/api/v1/vaults/provision", json=payload)
    assert first.status_code == 201

    second = client.post("/api/v1/vaults/provision", json=payload)
    assert second.status_code == 409
    assert second.json()["detail"] == "Hardware already provisioned"
