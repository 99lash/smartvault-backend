from typing import Dict, List
from fastapi import WebSocket

class WebSocketManager:
    # Manages active WebSocket connections, organized by User ID.
    # This allows us to push updates to specific users (e.g., "Alert Owner A").
    def __init__(self):
        # Maps user_id -> List of active WebSocket connections
        # (A user might have the dashboard open on both Laptop and Phone)
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        # Accepts a new WebSocket connection and registers it.
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        # Removes a connection when the client closes it.
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            
            # Clean up empty lists to save memory
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def broadcast_to_user(self, user_id: str, message: dict):
        # Sends a JSON message to all active devices for a specific user.
        if user_id in self.active_connections:
            # Iterate through all open tabs/apps for this user
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    # If sending fails (socket dead), we'll log it (or handle disconnect)
                    print(f"Error sending to {user_id}: {e}")

# Global instance to be imported elsewhere
manager = WebSocketManager()