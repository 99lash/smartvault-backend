# app/infrastructure/messaging/websocket_manager.py
"""
Enhanced WebSocket Manager for SmartVault.

Manages two types of connections:
1. User connections (web app, mobile app)
2. Vault device connections (ESP32 hardware)

Features:
- Connection registry (Redis-backed for horizontal scaling)
- Room-based broadcasting (vault_id rooms)
- Heartbeat monitoring
- Message routing by type
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from redis.asyncio import Redis

from app.application.ports.websocket_manager import WebSocketManagerPort
from app.domain.value_objects.websocket_messages import MessageType, WebSocketMessage

logger = logging.getLogger(__name__)


class ConnectionType:
    """Connection type identifiers"""
    USER = "user"
    VAULT = "vault"


class WebSocketManager(WebSocketManagerPort):
    """
    Manages WebSocket connections with support for:
    - Multiple user connections (same user, different devices)
    - Single vault device connections
    - Redis-backed connection registry (for multi-server deployments)
    - Room-based broadcasting
    """
    
    def __init__(self, redis: Optional[Redis] = None):
        # In-memory connection storage
        # user_connections: {user_id: [WebSocket, WebSocket, ...]}
        self.user_connections: Dict[str, List[WebSocket]] = {}
        
        # vault_connections: {vault_id: WebSocket}
        # Only ONE connection per vault device
        self.vault_connections: Dict[str, WebSocket] = {}
        
        # Connection metadata
        # connection_metadata: {connection_id: {type, user_id/vault_id, connected_at}}
        self.connection_metadata: Dict[str, dict] = {}
        
        # Vault subscriptions: {vault_id: {user_id, user_id, ...}}
        # Tracks which users are subscribed to which vaults
        self.vault_subscriptions: Dict[str, Set[str]] = {}
        
        # Redis client for distributed connection tracking (optional)
        self.redis = redis
        
        # Heartbeat tracking
        self.last_heartbeat: Dict[str, datetime] = {}
        
        # Start background tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start background tasks"""
        self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
        logger.info("WebSocket manager started")
    
    async def stop(self):
        """Stop background tasks"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        logger.info("WebSocket manager stopped")
    
    # ============================================
    # Connection Management - Users
    # ============================================
    
    async def connect_user(self, websocket: WebSocket, user_id: str):
        """Accept and register a user connection"""
        await websocket.accept()
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        
        self.user_connections[user_id].append(websocket)
        
        # Store metadata
        connection_id = id(websocket)
        self.connection_metadata[connection_id] = {
            "type": ConnectionType.USER,
            "user_id": user_id,
            "connected_at": datetime.now(timezone.utc),
        }
        
        # Register in Redis (for multi-server setup)
        if self.redis:
            await self.redis.sadd(f"user_connections:{user_id}", str(connection_id))
        
        logger.info(f"User {user_id} connected (total connections: {len(self.user_connections[user_id])})")
    
    def disconnect_user(self, websocket: WebSocket, user_id: str):
        """Remove a user connection"""
        if user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
            
            # Clean up empty lists
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Clean up metadata
        connection_id = id(websocket)
        if connection_id in self.connection_metadata:
            del self.connection_metadata[connection_id]
        
        # Clean up subscriptions
        for vault_id in list(self.vault_subscriptions.keys()):
            if user_id in self.vault_subscriptions[vault_id]:
                self.vault_subscriptions[vault_id].discard(user_id)
                if not self.vault_subscriptions[vault_id]:
                    del self.vault_subscriptions[vault_id]
        
        logger.info(f"User {user_id} disconnected")
    
    # ============================================
    # Connection Management - Vault Devices
    # ============================================
    
    async def connect_vault(self, websocket: WebSocket, vault_id: str):
        """Accept and register a vault device connection"""
        await websocket.accept()
        
        # Disconnect existing connection (only one per vault)
        if vault_id in self.vault_connections:
            old_ws = self.vault_connections[vault_id]
            await old_ws.close(code=1000, reason="New connection established")
            logger.warning(f"Vault {vault_id} reconnected, closing old connection")
        
        self.vault_connections[vault_id] = websocket
        
        # Store metadata
        connection_id = id(websocket)
        self.connection_metadata[connection_id] = {
            "type": ConnectionType.VAULT,
            "vault_id": vault_id,
            "connected_at": datetime.now(timezone.utc),
        }
        
        # Update heartbeat
        self.last_heartbeat[vault_id] = datetime.now(timezone.utc)
        
        # Register in Redis
        if self.redis:
            await self.redis.set(f"vault_connection:{vault_id}", str(connection_id))
            await self.redis.expire(f"vault_connection:{vault_id}", 300)  # 5 min expiry
        
        logger.info(f"Vault {vault_id} connected")
        
        # Notify subscribers that vault is online
        await self.broadcast_to_vault_subscribers(
            vault_id,
            {
                "type": MessageType.VAULT_STATUS_CHANGED.value,
                "payload": {
                    "vault_id": vault_id,
                    "status": "ONLINE",
                    "changed_at": datetime.now(timezone.utc).isoformat(),
                },
            },
        )
    
    def disconnect_vault(self, websocket: WebSocket, vault_id: str):
        """Remove a vault device connection"""
        if vault_id in self.vault_connections:
            if self.vault_connections[vault_id] == websocket:
                del self.vault_connections[vault_id]
        
        # Clean up metadata
        connection_id = id(websocket)
        if connection_id in self.connection_metadata:
            del self.connection_metadata[connection_id]
        
        # Clean up heartbeat
        if vault_id in self.last_heartbeat:
            del self.last_heartbeat[vault_id]
        
        logger.info(f"Vault {vault_id} disconnected")
    
    # ============================================
    # Message Sending
    # ============================================
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send message to all connections of a specific user"""
        if user_id not in self.user_connections:
            logger.debug(f"User {user_id} has no active connections")
            return
        
        dead_connections = []
        
        for connection in self.user_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to user {user_id}: {e}")
                dead_connections.append(connection)
        
        # Clean up dead connections
        for conn in dead_connections:
            self.disconnect_user(conn, user_id)
    
    async def send_to_vault(self, vault_id: str, message: dict):
        """Send message to a specific vault device"""
        if vault_id not in self.vault_connections:
            logger.warning(f"Vault {vault_id} is not connected")
            raise ConnectionError(f"Vault {vault_id} is offline")
        
        try:
            await self.vault_connections[vault_id].send_json(message)
            logger.debug(f"Sent message to vault {vault_id}: {message.get('type', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to send to vault {vault_id}: {e}")
            # Mark vault as disconnected
            self.disconnect_vault(self.vault_connections[vault_id], vault_id)
            raise
    
    async def broadcast_to_vault_subscribers(self, vault_id: str, message: dict):
        """
        Broadcast a message to all users subscribed to a vault.
        Used when vault status changes.
        """
        if vault_id not in self.vault_subscriptions:
            logger.debug(f"No subscribers for vault {vault_id}")
            return
        
        subscribers = list(self.vault_subscriptions[vault_id])
        logger.debug(f"Broadcasting to {len(subscribers)} subscribers of vault {vault_id}")
        
        for user_id in subscribers:
            await self.send_to_user(user_id, message)
    
    async def broadcast_to_all_users(self, message: dict):
        """Broadcast message to ALL connected users"""
        user_ids = list(self.user_connections.keys())
        for user_id in user_ids:
            await self.send_to_user(user_id, message)
    
    # ============================================
    # Subscription Management
    # ============================================
    
    def subscribe_to_vault(self, user_id: str, vault_id: str):
        """Subscribe a user to vault updates"""
        if vault_id not in self.vault_subscriptions:
            self.vault_subscriptions[vault_id] = set()
        
        self.vault_subscriptions[vault_id].add(user_id)
        logger.info(f"User {user_id} subscribed to vault {vault_id}")
    
    def unsubscribe_from_vault(self, user_id: str, vault_id: str):
        """Unsubscribe a user from vault updates"""
        if vault_id in self.vault_subscriptions:
            self.vault_subscriptions[vault_id].discard(user_id)
            if not self.vault_subscriptions[vault_id]:
                del self.vault_subscriptions[vault_id]
        
        logger.info(f"User {user_id} unsubscribed from vault {vault_id}")
    
    # ============================================
    # Status Queries
    # ============================================
    
    def is_vault_online(self, vault_id: str) -> bool:
        """Check if vault device is connected"""
        return vault_id in self.vault_connections
    
    def get_user_connection_count(self, user_id: str) -> int:
        """Get number of active connections for a user"""
        return len(self.user_connections.get(user_id, []))
    
    def get_online_vaults(self) -> list[str]:
        """Get list of all online vault IDs"""
        return list(self.vault_connections.keys())
    
    def get_connection_stats(self) -> dict:
        """Get connection statistics"""
        return {
            "total_users": len(self.user_connections),
            "total_user_connections": sum(len(conns) for conns in self.user_connections.values()),
            "total_vaults": len(self.vault_connections),
            "subscriptions": len(self.vault_subscriptions),
        }
    
    # ============================================
    # Background Tasks
    # ============================================
    
    async def _heartbeat_monitor(self):
        """
        Monitor vault heartbeats and mark as offline if no heartbeat received.
        Runs every 30 seconds.
        """
        while True:
            try:
                await asyncio.sleep(30)
                
                now = datetime.now(timezone.utc)
                offline_threshold = timedelta(minutes=2)
                
                for vault_id, last_beat in list(self.last_heartbeat.items()):
                    if now - last_beat > offline_threshold:
                        logger.warning(f"Vault {vault_id} heartbeat timeout, marking as offline")
                        
                        # Notify subscribers
                        await self.broadcast_to_vault_subscribers(
                            vault_id,
                            {
                                "type": MessageType.VAULT_STATUS_CHANGED.value,
                                "payload": {
                                    "vault_id": vault_id,
                                    "status": "OFFLINE",
                                    "changed_at": now.isoformat(),
                                },
                            },
                        )
                        
                        # Remove from connected vaults
                        if vault_id in self.vault_connections:
                            ws = self.vault_connections[vault_id]
                            self.disconnect_vault(ws, vault_id)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")


# Global instance
manager = WebSocketManager()