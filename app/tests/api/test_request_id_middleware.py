import uuid

from app.api.middleware.request_id import REQUEST_ID_HEADER


def test_response_includes_request_id_header(client):
    response = client.get("/api")

    request_id = response.headers.get(REQUEST_ID_HEADER)
    assert request_id
    uuid.UUID(request_id)


def test_request_id_is_unique_per_request(client):
    first = client.get("/api").headers.get(REQUEST_ID_HEADER)
    second = client.get("/api").headers.get(REQUEST_ID_HEADER)

    assert first
    assert second
    assert first != second


def test_preserves_client_provided_request_id(client):
    custom_id = "123e4567-e89b-12d3-a456-426614174000"

    response = client.get("/api", headers={REQUEST_ID_HEADER: custom_id})

    assert response.headers.get(REQUEST_ID_HEADER) == custom_id


def test_request_id_present_on_404(client):
    response = client.get("/api/does-not-exist")

    assert response.status_code == 404
    assert response.headers.get(REQUEST_ID_HEADER)


def test_auto_generated_request_id_is_uuid4(client):
    response = client.get("/api")
    request_id = response.headers.get(REQUEST_ID_HEADER)

    parsed = uuid.UUID(request_id)
    assert parsed.version == 4


def test_rejects_malformed_uuid(client):
    malformed_id = "not-a-valid-uuid"
    
    response = client.get("/api", headers={REQUEST_ID_HEADER: malformed_id})
    request_id = response.headers.get(REQUEST_ID_HEADER)
    
    # Should generate a new UUID, not use the malformed one
    assert request_id != malformed_id
    uuid.UUID(request_id)  # Should be valid UUID


def test_rejects_oversized_header(client):
    oversized_id = "a" * 100  # Far exceeds 36 char UUID limit
    
    response = client.get("/api", headers={REQUEST_ID_HEADER: oversized_id})
    request_id = response.headers.get(REQUEST_ID_HEADER)
    
    # Should generate a new UUID, not use oversized value
    assert request_id != oversized_id
    assert len(request_id) == 36
    uuid.UUID(request_id)


def test_rejects_log_injection_attempt(client):
    # Attempt to inject newlines to corrupt logs
    malicious_id = "abc123\nINJECTED LOG LINE\n"
    
    response = client.get("/api", headers={REQUEST_ID_HEADER: malicious_id})
    request_id = response.headers.get(REQUEST_ID_HEADER)
    
    # Should generate safe UUID, not the malicious input
    assert request_id != malicious_id
    assert "\n" not in request_id
    uuid.UUID(request_id)


def test_rejects_control_characters(client):
    malicious_id = "test\x00\x01\x02"
    
    response = client.get("/api", headers={REQUEST_ID_HEADER: malicious_id})
    request_id = response.headers.get(REQUEST_ID_HEADER)
    
    # Should generate safe UUID
    assert request_id != malicious_id
    uuid.UUID(request_id)


def test_rejects_empty_string(client):
    response = client.get("/api", headers={REQUEST_ID_HEADER: ""})
    request_id = response.headers.get(REQUEST_ID_HEADER)
    
    # Should generate a new UUID
    assert request_id
    uuid.UUID(request_id)


def test_accepts_valid_uuid_v1(client):
    # UUID v1 is also valid
    valid_id = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
    
    response = client.get("/api", headers={REQUEST_ID_HEADER: valid_id})
    
    assert response.headers.get(REQUEST_ID_HEADER) == valid_id