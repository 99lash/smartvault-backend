from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.infrastructure.messaging.websocket_manager import manager

# This is the 'router' variable the error is complaining about!
router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str = Query(...)
):
    
    # Handles the WebSocket lifecycle:
    # 1. Connect (Shake hands)
    # 2. Loop (Keep line open)
    # 3. Disconnect (Hang up)
    
    await manager.connect(websocket, user_id)
    try:
        while True:
            # We sit in this loop waiting for the client to say something.
            # Even if they say nothing, this keeps the connection alive.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)