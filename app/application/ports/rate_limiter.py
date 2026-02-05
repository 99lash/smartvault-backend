from abc import ABC, abstractmethod

class RateLimiter(ABC):
    @abstractmethod
    async def is_allowed(self, key: str) -> tuple[bool, int]:
        pass