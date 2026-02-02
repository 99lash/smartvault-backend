import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api import deps


@pytest.fixture(autouse=True)
def _clear_in_memory_user_repo():
    # prevents cross-test leakage because deps uses a singleton repo under pytest
    deps._in_memory_user_repo.clear()
    yield
    deps._in_memory_user_repo.clear()


def test_post_users_201():
    client = TestClient(app)

    r = client.post(
        "/api/v1/users",
        json={"email": "a@example.com", "password": "verylongpassword!", "full_name": "Alice"},
    )

    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == "a@example.com"
    assert body["full_name"] == "Alice"
    assert "password" not in body
    assert "password_hash" not in body


def test_post_users_409_duplicate():
    client = TestClient(app)

    client.post("/api/v1/users", json={"email": "a@example.com", "password": "verylongpassword!"})
    r = client.post("/api/v1/users", json={"email": "a@example.com", "password": "verylongpassword!"})

    assert r.status_code == 409, r.text


def test_post_users_422_invalid_payload():
    client = TestClient(app)

    # invalid email + short password
    r = client.post("/api/v1/users", json={"email": "not-an-email", "password": "short"})

    assert r.status_code == 422, r.text
