from enum import Enum


class VaultStatus(str, Enum):
    PROVISIONING = "PROVISIONING"
    LOCKED = "LOCKED"
    UNLOCKED = "UNLOCKED"
    OFFLINE = "OFFLINE"
