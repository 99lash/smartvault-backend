import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from app.main import app

client = TestClient(app)

def test_websocket_connection_success():
    
    # Test that we can connect when we provide the required 'user_id'.
    
    with client.websocket_connect("/api/v1/ws?user_id=test-user-123") as websocket:
        websocket.send_text("Ping")
        # If the code reaches here without crashing, the connection succeeded.
        assert True

def test_websocket_requires_user_id():
    
    # Test that the server rejects connection attempts missing the 'user_id'.
    
    # When the handshake fails (due to missing 422 param), 
    # TestClient raises a WebSocketDisconnect error.
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/v1/ws"):
            pass