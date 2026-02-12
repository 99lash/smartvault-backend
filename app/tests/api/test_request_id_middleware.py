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