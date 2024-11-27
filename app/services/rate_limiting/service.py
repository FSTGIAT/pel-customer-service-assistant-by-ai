class RateLimitService:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.rate_limit_window = 60  # 1 minute
        self.max_requests = 5  # requests per minute per user
        self.token_limit = 40000  # Claude's token limit

    async def check_rate_limit(self, customer_id: str) -> bool:
        """Check if request should be rate limited"""
        key = f"rate_limit:{customer_id}"
        current = await self.redis.get(key)
        
        if not current:
            # First request in window
            await self.redis.set(key, 1, expire=self.rate_limit_window)
            return True
        
        count = int(current)
        if count >= self.max_requests:
            return False
        
        # Increment count
        await self.redis.incr(key)
        return True

    async def get_token_count(self, content: str) -> int:
        """Estimate token count"""
        # Rough estimation: ~4 characters per token
        return len(content) // 4

    async def can_process_request(self, customer_id: str, content: str) -> tuple[bool, str]:
        """Check if request can be processed"""
        if not await self.check_rate_limit(customer_id):
            return False, "Rate limit exceeded. Please wait a minute."
            
        token_count = await self.get_token_count(content)
        if token_count > self.token_limit:
            return False, f"Content too long ({token_count} tokens). Please reduce content."
            
        return True, ""