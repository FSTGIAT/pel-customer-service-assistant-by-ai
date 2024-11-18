# app/core/redis.py
import redis
from app.core.config import settings
import json
from functools import wraps
from typing import Optional, Any

class RedisClient:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )

    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        return self.redis_client.get(key)

    async def set(self, key: str, value: str, ttl: int = None) -> bool:
        """Set value in Redis with optional TTL."""
        if ttl is None:
            ttl = settings.REDIS_TTL
        return self.redis_client.setex(key, ttl, value)

    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        return self.redis_client.delete(key)

# Create Redis client instance
redis_client = RedisClient()

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
