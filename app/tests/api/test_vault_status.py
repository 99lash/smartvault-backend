from fastapi.testclient import TestClient

from app.main import app


def test_get_vault_status_ok() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/vaults/demo-vault-1/status")

    assert response.status_code == 200
    body = response.json()
    assert body["vault_id"] == "demo-vault-1"
    assert body["status"] == "LOCKED"
    assert body["last_seen_at"] is not None


def test_get_vault_status_missing() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/vaults/does-not-exist/status")

    assert response.status_code == 404
    assert response.json()["detail"] == "Vault not found"
