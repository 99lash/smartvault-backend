from fastapi import APIRouter

from app.api.v1 import access, activity, auth, devices, health, users, vaults
from app.websocket import vault_socket

from app.api.internal.router import internal_router

# Root API router
api_router = APIRouter()

# Versioned API router
v1_router = APIRouter(prefix="/v1")

# HTTP (v1)
v1_router.include_router(health.router)
v1_router.include_router(vaults.router)
v1_router.include_router(users.router)
v1_router.include_router(auth.router)
v1_router.include_router(access.router)
v1_router.include_router(activity.router)
v1_router.include_router(devices.router)
# Attach v1 to root
api_router.include_router(v1_router)

# Internal admin API (requires X-Admin-Token)
api_router.include_router(internal_router)

# WEBSOCKET (versioned)
api_router.include_router(vault_socket.router, prefix="/v1", tags=["websockets"])
