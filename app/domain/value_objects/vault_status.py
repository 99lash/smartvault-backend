from enum import Enum


class VaultStatus(str, Enum):
    LOCKED = "LOCKED"
    UNLOCKED = "UNLOCKED"
    OFFLINE = "OFFLINE"
