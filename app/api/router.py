# collector/aggregator of all the endpoints so the main.py wont be cluttered with multiple endpoints

from fastapi import APIRouter
# HTTP IMPORTS
from app.api.v1 import health, vaults
# WEBSOCKET IMPORTS
from app.websocket import vault_socket

# HTTP
api_router = APIRouter()
api_router.include_router(health.router, prefix="/v1")
api_router.include_router(vaults.router, prefix="/v1")

# WEBSOCKET
api_router.include_router(vault_socket.router, prefix="/v1", tags=["websockets"])