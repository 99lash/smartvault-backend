from __future__ import annotations


def test_signup_happy_path(client, capture_email_service):
    email = "a@example.com"
    password = "verylongpassword!"
    full_name = "Alice Wonderland"

    # 1) Request OTP (sends email)
    r1 = client.post("/api/v1/auth/request-otp", json={"email": email})
    assert r1.status_code == 204, r1.text

    otp = capture_email_service.latest_otp_for(email)
    assert otp is not None
    assert len(otp) == 6

    # 2) Verify OTP -> returns signup ticket
    r2 = client.post("/api/v1/auth/verify-otp", json={"email": email, "otp": otp})
    assert r2.status_code == 200, r2.text
    ticket = r2.json()["signup_ticket"]
    assert isinstance(ticket, str) and len(ticket) >= 20

    # 3) Signup using ticket -> creates user
    r3 = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": password,
            "full_name": full_name,
            "signup_ticket": ticket,
        },
    )
    assert r3.status_code == 201, r3.text
    body = r3.json()
    assert body["email"] == email
    assert body["full_name"] == full_name
    assert "id" in body
    assert "created_at" in body


def test_signup_rejects_reused_ticket(client, capture_email_service):
    email = "b@example.com"
    password = "verylongpassword!"

    # request otp
    r1 = client.post("/api/v1/auth/request-otp", json={"email": email})
    assert r1.status_code == 204, r1.text
    otp = capture_email_service.latest_otp_for(email)
    assert otp is not None

    # verify otp -> ticket
    r2 = client.post("/api/v1/auth/verify-otp", json={"email": email, "otp": otp})
    assert r2.status_code == 200, r2.text
    ticket = r2.json()["signup_ticket"]

    # first signup ok
    r3 = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": password, "signup_ticket": ticket},
    )
    assert r3.status_code == 201, r3.text

    # second signup with same ticket should fail (ticket is one-time)
    r4 = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": password, "signup_ticket": ticket},
    )
    assert r4.status_code == 422, r4.text


def test_verify_otp_rejects_wrong_code(client):
    email = "c@example.com"

    # request otp
    r1 = client.post("/api/v1/auth/request-otp", json={"email": email})
    assert r1.status_code == 204, r1.text

    # wrong otp
    r2 = client.post("/api/v1/auth/verify-otp", json={"email": email, "otp": "000000"})
    assert r2.status_code == 422, r2.text
