import json
from typing import Any, Tuple, List

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

    # ==================== NEW METHODS ====================
    
    async def scan(
        self,
        cursor: int = 0,
        match: str = "*",
        count: int = 100,
    ) -> Tuple[int, List[str]]:
        """
        Scan Redis keys using cursor.
        
        Non-blocking alternative to KEYS command.
        
        Args:
            cursor: Starting cursor (0 for first call)
            match: Pattern to match (e.g., "model:*", "routing:*")
            count: Hint for number of keys per iteration
        
        Returns:
            Tuple of (next_cursor, list_of_keys)
        
        Example:
            cursor = 0
            all_keys = []
            while True:
                cursor, keys = await redis.scan(cursor, match="model:*")
                all_keys.extend(keys)
                if cursor == 0:
                    break
        """
        cursor, keys = await self.redis.scan(
            cursor=cursor,
            match=match,
            count=count
        )
        
        return cursor, keys

    async def keys(self, pattern: str = "*") -> List[str]:
        """
        Get all keys matching pattern.
        
        WARNING: Use with caution on large datasets.
        For production, prefer scan().
        
        Args:
            pattern: Key pattern (e.g., "model:*")
        
        Returns:
            List of matching keys
        """
        return await self.redis.keys(pattern)

    async def mget(self, keys: List[str]) -> List[str | None]:
        """
        Get multiple keys at once.
        
        More efficient than calling get() multiple times.
        
        Args:
            keys: List of keys to retrieve
        
        Returns:
            List of values (None for missing keys)
        """
        return await self.redis.mget(keys)

    async def lpush(self, key: str, value: str) -> int:
        """
        Push value to left of list.
        
        Returns:
            Length of list after push
        """
        return await self.redis.lpush(key, value)

    async def lrange(
        self,
        key: str,
        start: int = 0,
        stop: int = -1,
    ) -> List[str]:
        """
        Get range of values from list.
        
        Args:
            key: List key
            start: Start index (0-based)
            stop: Stop index (-1 for end)
        
        Returns:
            List of values
        """
        return await self.redis.lrange(key, start, stop)

    async def sadd(self, key: str, *values: str) -> int:
        """
        Add values to set.
        
        Returns:
            Number of elements added
        """
        return await self.redis.sadd(key, *values)

    async def smembers(self, key: str) -> set:
        """
        Get all members of set.
        
        Returns:
            Set of values
        """
        return await self.redis.smembers(key)

    async def incr(self, key: str) -> int:
        """
        Increment value by 1.
        Alias for increment(key, 1).
        
        Returns:
            New value
        """
        return await self.redis.incr(key)

    async def decr(self, key: str) -> int:
        """
        Decrement value by 1.
        
        Returns:
            New value
        """
        return await self.redis.decr(key)

    async def close(self):
        """
        Close Redis connection.
        """

        await self.redis.aclose()