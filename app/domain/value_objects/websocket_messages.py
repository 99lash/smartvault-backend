"""
WebSocket message types and protocols for SmartVault real-time communication.

Message Flow:
1. Client → Server: Commands, subscriptions
2. Server → Vault Device: Signed commands
3. Vault Device → Server: State updates, heartbeats
4. Server → Client: Broadcasts, notifications
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal


class MessageType(str, Enum):
    """WebSocket message types"""
    # Client → Server
    SUBSCRIBE = "SUBSCRIBE"           # Client wants updates for vault(s)
    UNSUBSCRIBE = "UNSUBSCRIBE"       # Client stops listening
    
    # Server → Vault Device
    COMMAND = "COMMAND"               # Execute action (unlock, lock, reboot)
    PING = "PING"                     # Keep-alive check
    
    # Vault Device → Server
    STATE_UPDATE = "STATE_UPDATE"     # Vault status changed
    HEARTBEAT = "HEARTBEAT"           # Device is alive
    TAMPER_ALERT = "TAMPER_ALERT"     # Security event detected
    
    # Server → Client
    VAULT_STATUS_CHANGED = "VAULT_STATUS_CHANGED"  # Broadcast status update
    NOTIFICATION = "NOTIFICATION"     # General notification
    ERROR = "ERROR"                   # Error message


class CommandAction(str, Enum):
    """Actions that can be commanded to vault devices"""
    UNLOCK = "UNLOCK"
    LOCK = "LOCK"
    REBOOT = "REBOOT"
    UPDATE_FIRMWARE = "UPDATE_FIRMWARE"


@dataclass
class WebSocketMessage:
    """Base message structure"""
    type: MessageType
    timestamp: datetime
    payload: dict[str, Any]
    
    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
        }


# Specific message payloads

@dataclass
class SubscribeMessage:
    """Client subscribes to vault updates"""
    vault_ids: list[str]  # Empty list = all vaults user owns


@dataclass
class CommandMessage:
    """Server sends command to vault device"""
    command_id: str
    action: CommandAction
    vault_id: str
    expires_at: datetime
    nonce: str
    signature: str  # HMAC-SHA256 of command data


@dataclass
class StateUpdateMessage:
    """Vault device reports state change"""
    vault_id: str
    status: str  # LOCKED, UNLOCKED, TAMPERED, etc.
    metadata: dict[str, Any]  # Additional info


@dataclass
class HeartbeatMessage:
    """Vault device keep-alive"""
    vault_id: str
    battery_level: int | None = None
    signal_strength: int | None = None
    firmware_version: str | None = None


@dataclass
class VaultStatusChangedMessage:
    """Broadcast to clients when vault status changes"""
    vault_id: str
    status: str
    changed_at: datetime
    changed_by: str | None  # user_id who triggered change


@dataclass
class NotificationMessage:
    """General notification to client"""
    title: str
    message: str
    severity: Literal["info", "warning", "error", "success"]
    vault_id: str | None = None


@dataclass
class ErrorMessage:
    """Error response"""
    error_code: str
    message: str
    details: dict[str, Any] | None = None