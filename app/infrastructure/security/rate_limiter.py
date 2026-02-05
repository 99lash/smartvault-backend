from fastapi import HTTPException, status
from app.infrastructure.cache.redis_client import get_redis

class RateLimitExceeded(HTTPException):
    def __init__(self, detail: str = "Too many requests. Please try again later."):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, 
            detail=detail
        )

class RateLimiter:
    """
    Vanilla Redis Fixed Window Rate Limiter.
    """
    async def allow_request(self, key: str, limit: int, window_seconds: int) -> None:
        """
        Checks if the request is allowed. Raises RateLimitExceeded if not.
        
        Args:
            key: Unique identifier (e.g., 'ip:127.0.0.1')
            limit: Max requests allowed in the window
            window_seconds: Time window in seconds
        """
        redis = await get_redis()
        redis_key = f"rate_limit:{key}"

        # Atomic INCR
        # Returns the new value after incrementing
        current_count = await redis.incr(redis_key)

        # If new key (count == 1), set the window expiry
        # Note: In a race condition where 2 requests hit simultaneously, 
        # both might see count > 1. We rely on the first one setting expiry.
        # To be robust, we set expiry if ttl is -1, but for this slice, 
        # setting on count==1 is the standard "Simple" pattern.
        if current_count == 1:
            await redis.expire(redis_key, window_seconds)
        
        if current_count > limit:
            raise RateLimitExceeded()