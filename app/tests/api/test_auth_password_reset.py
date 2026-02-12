from __future__ import annotations

import pytest
from datetime import datetime, timezone
from app.domain.models.user import User

def test_password_reset_happy_path(client, capture_email_service, user_repo):
    email = "reset@example.com"
    old_password = "oldpassword123!"
    new_password = "newpassword123!"
    
    # Setup: create a user
    client.post("/api/v1/auth/request-otp", json={"email": email})
    otp = capture_email_service.latest_otp_for(email)
    r_verify = client.post("/api/v1/auth/verify-otp", json={"email": email, "otp": otp})
    ticket = r_verify.json()["signup_ticket"]
    client.post("/api/v1/auth/signup", json={
        "email": email,
        "password": old_password,
        "signup_ticket": ticket
    })
    
    # 1. Request password reset
    r1 = client.post("/api/v1/auth/request-password-reset", json={"email": email})
    assert r1.status_code == 204
    
    token = capture_email_service.latest_token_for(email)
    assert token is not None
    
    # 2. Confirm password reset
    r2 = client.post("/api/v1/auth/confirm-password-reset", json={
        "token": token,
        "new_password": new_password
    })
    assert r2.status_code == 204
    
    # 3. Verify login with new password
    r3 = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": new_password
    })
    assert r3.status_code == 200
    assert "access_token" in r3.json()
    
    # 4. Verify old password no longer works
    r4 = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": old_password
    })
    assert r4.status_code == 401

def test_password_reset_unknown_email(client, capture_email_service):
    email = "unknown@example.com"
    
    r1 = client.post("/api/v1/auth/request-password-reset", json={"email": email})
    assert r1.status_code == 204
    
    # No email should be sent
    token = capture_email_service.latest_token_for(email)
    assert token is None

def test_password_reset_invalid_token(client):
    r1 = client.post("/api/v1/auth/confirm-password-reset", json={
        "token": "invalid-token-that-is-long-enough-for-pydantic",
        "new_password": "newpassword123!"
    })
    assert r1.status_code == 422
    assert "Invalid or expired reset token" in r1.json()["detail"]

def test_password_reset_token_reuse_fails(client, capture_email_service, user_repo):
    email = "reuse@example.com"
    password = "password123456"
    
    # Setup: create user
    client.post("/api/v1/auth/request-otp", json={"email": email})
    otp = capture_email_service.latest_otp_for(email)
    ticket = client.post("/api/v1/auth/verify-otp", json={"email": email, "otp": otp}).json()["signup_ticket"]
    client.post("/api/v1/auth/signup", json={"email": email, "password": password, "signup_ticket": ticket})
    
    # Request reset
    client.post("/api/v1/auth/request-password-reset", json={"email": email})
    token = capture_email_service.latest_token_for(email)
    
    # Use token once
    r1 = client.post("/api/v1/auth/confirm-password-reset", json={
        "token": token,
        "new_password": "newpassword123!"
    })
    assert r1.status_code == 204
    
    # Use token again
    r2 = client.post("/api/v1/auth/confirm-password-reset", json={
        "token": token,
        "new_password": "anotherpassword123!"
    })
    assert r2.status_code == 422
    assert "Invalid or expired reset token" in r2.json()["detail"]

def test_password_reset_password_too_short(client, capture_email_service, user_repo):
    email = "short@example.com"
    password = "password123456"
    
    # Setup: create user
    client.post("/api/v1/auth/request-otp", json={"email": email})
    otp = capture_email_service.latest_otp_for(email)
    ticket = client.post("/api/v1/auth/verify-otp", json={"email": email, "otp": otp}).json()["signup_ticket"]
    client.post("/api/v1/auth/signup", json={"email": email, "password": password, "signup_ticket": ticket})
    
    # Request reset
    client.post("/api/v1/auth/request-password-reset", json={"email": email})
    token = capture_email_service.latest_token_for(email)
    
    # Confirm with short password
    r1 = client.post("/api/v1/auth/confirm-password-reset", json={
        "token": token,
        "new_password": "short"
    })
    # Pydantic should catch this first if min_length=12
    assert r1.status_code == 422
