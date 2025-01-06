from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List
import asyncio
import uuid
import logging
from app.core.redis import redis_client 
import json

logger = logging.getLogger(__name__)

class MessageEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)


@dataclass
class QueuedClaudeRequest:
    id: str
    customer_id: str
    message: str
    context: List[Dict]
    pdf_context: Optional[str]
    timestamp: datetime
    token_estimate: int

class RateLimitService:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.rate_limit_window = 60
        self.max_requests = 5
        self.token_limit = 40000
        self.queue_key = "claude_queue"
        self.usage_key = "claude_token_usage"

    async def queue_claude_request(
        self, 
        customer_id: str, 
        message: str, 
        context: List[Dict],
        pdf_context: Optional[str] = None
    ) -> str:
        """Queue a request for processing"""
        try:
            request_id = str(uuid.uuid4())
            
            # Convert Message objects to dictionaries
            context_data = [
                {
                    "type": msg.get("type", "unknown"),
                    "content": msg.get("content", "")
                } for msg in (context or [])
            ]
            
            request_data = {
                "id": request_id,
                "customer_id": customer_id,
                "message": message,
                "context": json.dumps(context_data),
                "timestamp": datetime.now().isoformat()
            }
            
            await self.redis.zadd(
                self.queue_key,
                {request_id: datetime.now().timestamp()}
            )
            
            await self.redis.hset(
                f"claude_request:{request_id}",
                mapping=request_data
            )
            
            logger.debug(f"Queued request {request_id} for customer {customer_id}")
            return request_id
            
        except Exception as e:
            logger.error(f"Error queueing request: {e}")
            raise

    async def can_process_request(self, customer_id: str, content: str) -> tuple[bool, str]:
        """Check if request can be processed based on rate limits and token count"""
        try:
            # Get current request count
            key = f"rate_limit:{customer_id}"
            current = await self.redis.get(key)
            current_count = int(current) if current else 0

            # Check request limit
            if current_count >= self.max_requests:
                return False, "נא להמתין דקה לפני שליחת בקשה נוספת"

            # Increment counter and set expiry if first request
            await self.redis.incr(key)
            if current_count == 0:
                await self.redis.expire(key, self.rate_limit_window)

            # Token usage check
            try:
                current_usage = 0
                usage_key = f"token_usage:{customer_id}"
                stored_usage = await self.redis.get(usage_key)
                if stored_usage:
                    current_usage = int(stored_usage)

                token_estimate = len(content) // 4

                if current_usage + token_estimate > self.token_limit:
                    return False, "נא להמתין מעט, המערכת עמוסה כרגע"

                # Update token usage - using separate set and expire calls
                await self.redis.set(usage_key, str(current_usage + token_estimate))
                await self.redis.expire(usage_key, self.rate_limit_window)

            except Exception as e:
                logger.error(f"Token check error: {e}")

            return True, ""

        except Exception as e:
            logger.error(f"Rate limit error: {e}")
            return True, ""

    @classmethod
    def create(cls):
        """Factory method to create service instance with redis client"""
        return cls(redis_client)

    async def check_rate_limit(self, customer_id: str) -> bool:
        key = f"rate_limit:{customer_id}"

        try:
            current = await self.redis.get(key)
        
            if not current:
                await self.redis.set(key, 1, expire=self.rate_limit_window)
                return True
        
            count = int(current)
            if count >= self.max_requests:
                return False
            
            await self.redis.incr(key)
            return True
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True  # Allow on error

    async def get_token_count(self, content: str) -> int:
        return len(content) // 4


    async def get_queue_position(self, request_id: str) -> Optional[int]:
        """Get position in queue"""
        return await self.redis.zrank(self.queue_key, request_id)

    async def _get_token_usage(self) -> int:
        window_start = datetime.now().timestamp() - self.rate_limit_window
        count = await self.redis.zcount(
            self.usage_key,
            min=window_start,
            max="+inf"
        )
        return count if count is not None else 0

async def process_claude_queue(self):
    """Process queued requests"""
    while True:
        try:
            # Get next request in queue
            next_request = await self.redis.zrange(
                self.queue_key,
                0, 0,
                withscores=True
            )

            if not next_request:
                await asyncio.sleep(0.1)
                continue

            request_id = next_request[0][0]
            request_data = await self.redis.hgetall(f"claude_request:{request_id}")

            if not request_data:
                # Remove invalid request
                await self.redis.zrem(self.queue_key, request_id)
                continue

            # Remove from queue immediately to prevent duplicates
            await self.redis.zrem(self.queue_key, request_id)
            await self.redis.delete(f"claude_request:{request_id}")

            logger.info(f"Processed request {request_id} from queue")

        except Exception as e:
            logger.error(f"Error processing queue: {e}")
            await asyncio.sleep(1)

    async def _get_token_usage(self) -> int:
        window_start = datetime.now().timestamp() - self.rate_limit_window
        return await self.redis.zcount(
            self.usage_key,
            min=window_start,
            max="+inf"
        )

    async def _update_token_usage(self, tokens: int):
        now = datetime.now().timestamp()
        await self.redis.zadd(self.usage_key, {str(now): tokens})
        await self._cleanup_old_usage()

    async def _cleanup_old_usage(self):
        window_start = datetime.now().timestamp() - self.rate_limit_window
        await self.redis.zremrangebyscore(self.usage_key, "-inf", window_start)




rate_limit_service = RateLimitService.create()


# Export the instance
__all__ = ['rate_limit_service']