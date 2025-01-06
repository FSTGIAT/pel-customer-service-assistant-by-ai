from typing import Optional, Dict, Any
import asyncio
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class MessageQueueService:
    def __init__(self, redis_client, max_queue_size: int = 100):
        self.redis = redis_client
        self.max_queue_size = max_queue_size
        self.queue_key = "chat_request_queue"
        self.processing_key = "chat_processing"
        self.result_ttl = 300  # 5 minutes

    async def enqueue_message(self, 
        message: str, 
        customer_id: str, 
        pdf_content: str
    ) -> str:
        """Add message to queue and return request ID"""
        try:
            request_id = f"{customer_id}_{datetime.utcnow().timestamp()}"
            queue_data = {
                'id': request_id,
                'message': message,
                'customer_id': customer_id,
                'pdf_content': pdf_content,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'pending'
            }

            # Add to queue
            await self.redis.lpush(
                self.queue_key,
                json.dumps(queue_data)
            )

            # Trim queue if too long
            await self.redis.ltrim(self.queue_key, 0, self.max_queue_size - 1)

            return request_id

        except Exception as e:
            logger.error(f"Error enqueueing message: {e}")
            raise

    async def get_request_status(self, request_id: str) -> Dict[str, Any]:
        """Get status of a request"""
        try:
            # Check processing requests
            processing = await self.redis.hget(self.processing_key, request_id)
            if processing:
                return {'status': 'processing', 'data': json.loads(processing)}

            # Check completed results
            result = await self.redis.get(f"result:{request_id}")
            if result:
                return {'status': 'completed', 'data': json.loads(result)}

            # Check queue
            queue_length = await self.redis.llen(self.queue_key)
            queue_items = await self.redis.lrange(self.queue_key, 0, queue_length - 1)
            
            for item in queue_items:
                data = json.loads(item)
                if data['id'] == request_id:
                    position = queue_items.index(item)
                    return {
                        'status': 'queued',
                        'position': position + 1,
                        'data': data
                    }

            return {'status': 'not_found'}

        except Exception as e:
            logger.error(f"Error getting request status: {e}")
            return {'status': 'error', 'message': str(e)}

    async def store_result(self, request_id: str, result: str) -> None:
        """Store processed result"""
        try:
            await self.redis.set(
                f"result:{request_id}",
                json.dumps({
                    'result': result,
                    'timestamp': datetime.utcnow().isoformat()
                }),
                expire=self.result_ttl
            )
            # Remove from processing
            await self.redis.hdel(self.processing_key, request_id)
        except Exception as e:
            logger.error(f"Error storing result: {e}")
            raise

    async def process_next(self) -> Optional[Dict[str, Any]]:
        """Get next message from queue"""
        try:
            raw_data = await self.redis.rpop(self.queue_key)
            if not raw_data:
                return None

            data = json.loads(raw_data)
            # Mark as processing
            await self.redis.hset(
                self.processing_key,
                data['id'],
                json.dumps({
                    **data,
                    'processing_started': datetime.utcnow().isoformat()
                })
            )
            return data

        except Exception as e:
            logger.error(f"Error processing next message: {e}")
            return None