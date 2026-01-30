import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from app.main import app

client = TestClient(app)

def test_websocket_connection_success():
    """
    Test that we can connect. 
    Note: 'user_id' is now injected by the dependency, so we don't need to send it in the URL.
    """
    with client.websocket_connect("/api/v1/ws/user") as websocket:
        websocket.send_text("Ping")
        assert True

def test_websocket_validates_dependency():
    """
    If we had real auth, we would test that invalid tokens fail here.
    For now, since get_current_user_id always returns a user, 
    we just verify the connection opens successfully.
    """
    with client.websocket_connect("/api/v1/ws/user") as websocket:
        assert True