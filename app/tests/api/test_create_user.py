import pytest


def test_post_users_201(client):
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


def test_post_users_409_duplicate(client):
    r1 = client.post(
        "/api/v1/users",
        json={"email": "a@example.com", "password": "verylongpassword!"},
    )
    assert r1.status_code == 201, r1.text

    r2 = client.post(
        "/api/v1/users",
        json={"email": "a@example.com", "password": "verylongpassword!"},
    )
    assert r2.status_code == 409, r2.text



def test_post_users_422_invalid_payload(client):
    # invalid email + short password
    r = client.post("/api/v1/users", json={"email": "not-an-email", "password": "short"})

    assert r.status_code == 422, r.text
