"""
Session and refresh token metrics.

Uses SYNC Redis with connection pooling for efficient resource management.
Matches the pattern used in redis_client.py for consistency.

Clean Architecture:
    Infrastructure layer — reads from and writes to Redis directly.
    No domain or application logic.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from redis import Redis, ConnectionPool

from app.core.settings import settings


# =============================================================================
# CONNECTION POOL (Lazy Singleton)
# =============================================================================

_pool: Optional[ConnectionPool] = None


def _get_pool() -> ConnectionPool:
    """
    Get or create the Redis connection pool.
    
    Uses lazy initialization to avoid creating the pool until needed.
    Thread-safe for concurrent access in sync context.
    
    Returns:
        Shared ConnectionPool instance.
    """
    global _pool
    if _pool is None:
        _pool = ConnectionPool.from_url(
            str(settings.REDIS_URL),
            decode_responses=False,
            max_connections=10,  # Limit connections for this module
        )
    return _pool


def _sync_redis() -> Redis:
    """
    Get a Redis client from the shared connection pool.
    
    Each call reuses a connection from the pool rather than
    creating a new TCP connection.
    
    Returns:
        Redis client using shared connection pool.
    """
    return Redis(connection_pool=_get_pool(), decode_responses=False)


def close_session_metrics_pool() -> None:
    """
    Close all connections in the pool.
    
    Call during application shutdown to release resources cleanly.
    """
    global _pool
    if _pool is not None:
        _pool.disconnect()
        _pool = None


# =============================================================================
# DOMAIN TYPES
# =============================================================================

@dataclass(frozen=True)
class SessionMetrics:
    """Refresh token session statistics."""
    total_active_tokens: int
    top_users: list[dict]


# =============================================================================
# OPERATIONS
# =============================================================================

def get_session_metrics() -> SessionMetrics:
    """
    Scan Redis for refresh:* keys and count tokens per user.

    Keys are written by RedisRefreshTokenStore as:
        refresh:<token>  →  <user_id>

    Returns:
        SessionMetrics with total token count and top 10 users by count.
    """
    redis = _sync_redis()

    user_token_counts: dict[str, int] = {}
    total_tokens = 0

    cursor = 0
    while True:
        cursor, keys = redis.scan(cursor=cursor, match=b"refresh:*", count=100)

        for raw_key in keys:
            total_tokens += 1
            raw_value = redis.get(raw_key)
            if raw_value:
                user_id = (
                    raw_value.decode("utf-8")
                    if isinstance(raw_value, bytes)
                    else raw_value
                )
                user_token_counts[user_id] = user_token_counts.get(user_id, 0) + 1

        if cursor == 0:
            break

    top_users = sorted(
        [
            {"user_id": uid, "token_count": count}
            for uid, count in user_token_counts.items()
        ],
        key=lambda x: x["token_count"],
        reverse=True,
    )[:10]

    return SessionMetrics(
        total_active_tokens=total_tokens,
        top_users=top_users,
    )


def revoke_user_sessions(user_id: str) -> int:
    """
    Revoke all refresh tokens belonging to a specific user.

    Scans refresh:* keys, reads the stored user_id value,
    and deletes matching keys.

    Args:
        user_id: The user whose sessions to revoke.

    Returns:
        Number of tokens revoked.
    """
    redis = _sync_redis()
    revoked = 0

    cursor = 0
    while True:
        cursor, keys = redis.scan(cursor=cursor, match=b"refresh:*", count=100)

        for raw_key in keys:
            raw_value = redis.get(raw_key)
            if raw_value:
                stored_uid = (
                    raw_value.decode("utf-8")
                    if isinstance(raw_value, bytes)
                    else raw_value
                )
                if stored_uid == user_id:
                    redis.delete(raw_key)
                    revoked += 1

        if cursor == 0:
            break

    return revoked
