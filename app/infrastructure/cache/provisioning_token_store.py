from __future__ import annotations

from app.application.ports.provisioning_token_store import ProvisioningTokenStore
from app.infrastructure.cache.redis_client import get_redis


class RedisProvisioningTokenStore(ProvisioningTokenStore):
    def _key(self, token: str) -> str:
        return f"prov:{token}"

    async def set(self, token: str, user_id: str, ttl_seconds: int) -> bool:
        r = await get_redis()
        result = await r.set(self._key(token), user_id.encode(), nx=True, ex=ttl_seconds)
        return result is not None

    async def get(self, token: str) -> str | None:
        r = await get_redis()
        value = await r.get(self._key(token))
        if value is None:
            return None
        return value.decode()

    async def delete(self, token: str) -> None:
        r = await get_redis()
        await r.delete(self._key(token))
