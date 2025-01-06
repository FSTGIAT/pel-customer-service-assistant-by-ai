# app/core/redis.py
import redis
from app.core.config import settings
import json
from functools import wraps
from typing import Optional, Any, Dict, List, Union, Set

class RedisClient:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_SESSION_HOST,  # Using your existing session settings
            port=settings.REDIS_SESSION_PORT,
            db=settings.REDIS_SESSION_DB,
            decode_responses=True
        )

    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        return self.redis_client.get(key)

    async def set(self, key: str, value: str, ttl: int = None) -> bool:
        """Set value in Redis with optional TTL."""
        if ttl is None:
            ttl = settings.SESSION_TIMEOUT
        return self.redis_client.setex(key, ttl, value)

    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        return self.redis_client.delete(key)

    async def incr(self, key: str) -> int:
        """Increment value for rate limiting."""
        return self.redis_client.incr(key)

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiry on key."""
        return self.redis_client.expire(key, seconds)
    # New sorted set methods
    async def zadd(self, key: str, mapping: Dict[str, float]) -> int:
        return self.redis_client.zadd(key, mapping)

    async def zcount(self, key: str, min: Union[float, str], max: Union[float, str]) -> int:
        return self.redis_client.zcount(key, min, max)

    async def zrange(self, key: str, start: int, stop: int, withscores: bool = False) -> List:
        return self.redis_client.zrange(key, start, stop, withscores=withscores)

    async def zrank(self, key: str, member: str) -> Optional[int]:
        return self.redis_client.zrank(key, member)

    async def zrem(self, key: str, member: str) -> int:
        return self.redis_client.zrem(key, member)

    async def zremrangebyscore(self, key: str, min: Union[float, str], max: Union[float, str]) -> int:
        return self.redis_client.zremrangebyscore(key, min, max)
    # Hash methods
    async def hset(self, key: str, mapping: Dict[str, str]) -> int:
        return self.redis_client.hset(key, mapping=mapping)

    async def hget(self, key: str, field: str) -> Optional[str]:
        return self.redis_client.hget(key, field)

    async def hgetall(self, key: str) -> Dict[str, str]:
        return self.redis_client.hgetall(key)

    async def exists(self, key: str) -> bool:
        return bool(self.redis_client.exists(key))

    async def ttl(self, key: str) -> int:
        """Get TTL for key."""
        return self.redis_client.ttl(key)

    async def zcard(self, key: str) -> int:
        """Get number of members in a sorted set."""
        return self.redis_client.zcard(key)

    async def zscore(self, key: str, member: str) -> Optional[float]:
        """Get score of member in sorted set."""
        return self.redis_client.zscore(key, member)

    async def multi_get(self, keys: List[str]) -> List[Optional[str]]:
        """Get multiple values at once."""
        pipe = self.redis_client.pipeline()
        for key in keys:
            pipe.get(key)
        return pipe.execute()

    async def hincrby(self, key: str, field: str, amount: int = 1) -> int:
        """Increment the integer value of a hash field by the given number."""
        return self.redis_client.hincrby(key, field, amount)

    async def pipeline(self):
        """Get a pipeline object for batch operations."""
        return self.redis_client.pipeline()

    async def hmset(self, key: str, mapping: Dict[str, Any]) -> bool:
        """Set multiple hash fields to multiple values."""
        return self.redis_client.hmset(key, mapping)

    async def sadd(self, key: str, *values: str) -> int:
        """Add one or more members to a set."""
        return self.redis_client.sadd(key, *values)

    async def smembers(self, key: str) -> Set[str]:
        """Get all members in a set."""
        return self.redis_client.smembers(key)

    async def srem(self, key: str, *values: str) -> int:
        """Remove one or more members from a set."""
        return self.redis_client.srem(key, *values)


# Create Redis client instance
redis_client = RedisClient()
__all__ = ['redis_client']

# Cache decorator
def cache_response(ttl: int = None):
    """
    Decorator to cache function responses in Redis.
    
    Usage:
        @cache_response(ttl=3600)
        async def my_function(arg1, arg2):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = await redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await redis_client.set(
                cache_key,
                json.dumps(result),
                ttl=ttl or settings.REDIS_TTL
            )
            return result
        return wrapper
    return decorator
