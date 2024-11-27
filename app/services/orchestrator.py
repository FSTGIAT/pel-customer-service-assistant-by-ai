from typing import Optional, Dict
import logging
from .rate_limiting.service import RateLimitService
from .pdf_content.service import PDFContentService
from .response_cache.service import ResponseCacheService
from .message_queue.service import MessageQueueService
from .claude_service import claude_service

logger = logging.getLogger(__name__)

class ChatOrchestrator:
    def __init__(self, redis_client, db):
        self.rate_limit = RateLimitService(redis_client)
        self.pdf_content = PDFContentService(db, redis_client)
        self.response_cache = ResponseCacheService(redis_client)
        self.message_queue = MessageQueueService(redis_client)

    async def process_chat_request(self, message: str, customer_id: str, pdfs: list) -> Dict:
        """Process chat request with all optimizations"""
        try:
            # 1. Check rate limit
            can_process, limit_message = await self.rate_limit.can_process_request(customer_id, message)
            if not can_process:
                return {"status": "rate_limited", "message": limit_message}

            # 2. Get optimized PDF content
            pdf_paths = [pdf.path for pdf in pdfs]
            relevant_content = await self.pdf_content.get_relevant_content(message, pdf_paths)

            # 3. Check cache
            cached_response = await self.response_cache.get_cached_response(message, relevant_content)
            if cached_response:
                logger.info(f"Cache hit for customer {customer_id}")
                return {"status": "success", "response": cached_response, "source": "cache"}

            # 4. Queue request if needed
            request_id = await self.message_queue.enqueue_message(message, customer_id, relevant_content)
            
            # 5. Process immediately if possible
            request_status = await self.message_queue.get_request_status(request_id)
            
            if request_status['status'] == 'queued' and request_status['position'] > 1:
                return {
                    "status": "queued",
                    "message": f"Request queued at position {request_status['position']}",
                    "request_id": request_id
                }

            # 6. Process request
            response = await claude_service.get_response(
                message=message,
                pdf_content=relevant_content
            )

            # 7. Cache response
            await self.response_cache.cache_response(message, relevant_content, response)
            await self.message_queue.store_result(request_id, response)

            return {
                "status": "success",
                "response": response,
                "source": "claude",
                "request_id": request_id
            }

        except Exception as e:
            logger.error(f"Error processing chat request: {e}")
            raise