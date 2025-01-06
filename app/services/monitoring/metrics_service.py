# app/services/monitoring/metrics_service.py

from typing import Dict, Optional, List
from datetime import datetime
import logging
from app.core.redis import redis_client
from app.core.database import db
from dataclasses import dataclass


logger = logging.getLogger(__name__)

@dataclass
class TokenUsage:
    used: int
    remaining: int
    reset_time: datetime

@dataclass
class RateLimitMetrics:
    queue_length: int
    rate_limited_requests: int
    token_usage: int
    avg_response_time: float

@dataclass
class QueueMetrics:
    total_queued: int
    pending_requests: int
    avg_wait_time: float



class MetricsService:
    def __init__(self):
        self.update_interval = 5  # 5 seconds
        self.token_limit = 40000  # Claude's rate limit per minute
        
        
    async def get_rate_limit_metrics(self, customer_id: str) -> RateLimitMetrics:
        """Get current rate limiting metrics for a customer."""
        try:
            # Use multi_get for better performance
            keys = [
                f"claude_queue:{customer_id}",
                f"rate_limit:{customer_id}",
                f"token_usage:{customer_id}",
                f"avg_response_time:{customer_id}"
            ]
            
            results = await redis_client.multi_get(keys)
            queue_length = await redis_client.zcard(f"claude_queue:{customer_id}")
            
            return RateLimitMetrics(
                queue_length=queue_length or 0,
                rate_limited_requests=int(results[1] or 0),
                token_usage=int(results[2] or 0),
                avg_response_time=float(results[3] or 0)
            )
        except Exception as e:
            logger.error(f"Error fetching rate limit metrics: {str(e)}")
            return RateLimitMetrics(0, 0, 0, 0.0)
            
    async def get_queue_metrics(self) -> QueueMetrics:
        """Get current queue metrics."""
        try:
            total_queued = await redis_client.zcard("claude_queue")
            pending = await redis_client.zcount(
                "claude_queue", 
                "-inf", 
                str(datetime.now().timestamp())
            )
            avg_wait = await self._calculate_average_wait_time()

            return QueueMetrics(
                total_queued=int(total_queued or 0),
                pending_requests=int(pending or 0),
                avg_wait_time=float(avg_wait)
            )
        except Exception as e:
            logger.error(f"Error fetching queue metrics: {str(e)}")
            return QueueMetrics(0, 0, 0.0)

    async def get_token_usage(self, customer_id: str) -> TokenUsage:
        """Get Claude API token usage metrics."""
        try:
            token_key = f"token_usage:{customer_id}"
            
            # Get multiple values at once
            usage, ttl = await redis_client.multi_get([
                token_key,
                f"rate_limit:{customer_id}"
            ])
            
            usage_int = int(usage) if usage else 0
            ttl_int = await redis_client.ttl(token_key)
            reset_time = datetime.now().timestamp() + (ttl_int if ttl_int > 0 else 60)

            return TokenUsage(
                used=usage_int,
                remaining=max(0, self.token_limit - usage_int),
                reset_time=datetime.fromtimestamp(reset_time)
            )
        except Exception as e:
            logger.error(f"Error fetching token usage: {str(e)}")
            return TokenUsage(
                used=0,
                remaining=self.token_limit,
                reset_time=datetime.fromtimestamp(datetime.now().timestamp() + 60)
            )
    async def _calculate_average_wait_time(self) -> float:
        """Calculate average wait time for requests in queue."""
        try:
            recent_requests = await redis_client.zrange(
                "claude_queue", 
                0, 
                -1, 
                withscores=True
            )
            
            if not recent_requests:
                return 0.0

            total_wait = sum(float(score) for _, score in recent_requests)
            return total_wait / len(recent_requests)
        except Exception as e:
            logger.error(f"Error calculating average wait time: {str(e)}")
            return 0.0

    async def store_metrics_in_db(self, customer_id: str, metrics: RateLimitMetrics):
        """Store metrics in PostgreSQL for historical analysis."""
        try:
            query = """
                INSERT INTO telecom.rate_limit_metrics
                (customer_id, queue_length, rate_limited_requests, 
                 token_usage, avg_response_time, created_at)
                VALUES ($1, $2, $3, $4, $5, NOW())
            """
            await db.execute(
                query,
                customer_id,
                metrics.queue_length,
                metrics.rate_limited_requests,
                metrics.token_usage,
                metrics.avg_response_time
            )
        except Exception as e:
            logger.error(f"Error storing metrics in database: {str(e)}")

# Create singleton instance
metrics_service = MetricsService()