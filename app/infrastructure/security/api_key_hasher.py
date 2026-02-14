"""
API key generation and hashing utilities.

Follows the pattern established by password_hasher.py and pin_hasher.py
in infrastructure/security/.

Design:
    - Keys use secrets.token_urlsafe(32) for cryptographic randomness
    - Hashing uses SHA-256 (fast, sufficient for random high-entropy tokens)
    - Prefix "sk_" makes keys identifiable in logs/config

Clean Architecture:
    Infrastructure layer — security utilities only.
    No domain or application logic.
"""
from __future__ import annotations

import hashlib
import secrets


def generate_api_key() -> str:
    """
    Generate a new cryptographically random API key.

    Returns:
        A prefixed URL-safe key string (e.g. sk_abc123...).
    """
    return f"sk_{secrets.token_urlsafe(32)}"


def hash_api_key(key: str) -> str:
    """
    Hash an API key for secure storage.

    Uses SHA-256. Safe for high-entropy random tokens — bcrypt/argon2
    are unnecessary overhead here since tokens are already 256 bits of
    entropy (unlike passwords chosen by humans).

    Args:
        key: The plain API key.

    Returns:
        Hex-encoded SHA-256 hash.
    """
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(key: str, key_hash: str) -> bool:
    """
    Verify a plain API key against its stored hash.

    Args:
        key:      The plain API key to verify.
        key_hash: The stored SHA-256 hash.

    Returns:
        True if the key matches the hash.
    """
    return hash_api_key(key) == key_hash
