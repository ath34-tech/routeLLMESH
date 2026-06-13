import json
from typing import Any

from app.core.redis.client import redis_client


class RedisRepository:
    """
    Generic Redis repository for storing and retrieving JSON data.
    """

    def __init__(self):
        self.redis = redis_client

    async def get_json(self, key: str) -> dict[str, Any] | None:
        """
        Retrieve JSON object from Redis.

        Returns:
            dict if found else None
        """

        value = await self.redis.get(key)

        if value is None:
            return None

        return json.loads(value)

    async def set_json(
        self,
        key: str,
        value: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """
        Store JSON object in Redis.

        ttl:
            None -> no expiration
            seconds -> expire after ttl
        """

        serialized = json.dumps(value)

        if ttl is None:
            await self.redis.set(key, serialized)
        else:
            await self.redis.set(key, serialized, ex=ttl)

    async def delete(self, key: str) -> None:
        """
        Delete key from Redis.
        """

        await self.redis.delete(key)

    async def exists(self, key: str) -> bool:
        """
        Check whether key exists.
        """

        return bool(await self.redis.exists(key))

    async def expire(
        self,
        key: str,
        ttl: int,
    ) -> None:
        """
        Set expiration for an existing key.
        """

        await self.redis.expire(key, ttl)

    async def increment(
        self,
        key: str,
        amount: int = 1,
    ) -> int:
        """
        Atomic increment.

        Useful for:
        - rate limiting
        - metrics
        - counters
        """

        return await self.redis.incrby(key, amount)

    async def close(self):
        """
        Close Redis connection.
        """

        await self.redis.aclose()


    async def set(
        self,
        key: str,
        value: str,
        ttl: int | None = None,
    ):

        if ttl is None:
            await self.redis.set(key, value)
        else:
            await self.redis.set(key, value, ex=ttl)


    async def get(
        self,
        key: str,
    ) -> str | None:

        return await self.redis.get(key)
    
    async def set_if_not_exists(
        self,
        key: str,
        value: str,
        ttl: int,
    ) -> bool:

        return await self.redis.set(
            key,
            value,
            ex=ttl,
            nx=True,
        )
    
    async def ttl(
        self,
        key: str,
    ) -> int:

        return await self.redis.ttl(key)