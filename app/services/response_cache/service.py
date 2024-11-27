from typing import Optional, Dict
import json
import hashlib
from datetime import datetime

class ResponseCacheService:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.cache_ttl = 3600  # 1 hour cache
        self.cache_prefix = "chat_response:"

    async def get_cached_response(self, message: str, pdf_content: str) -> Optional[str]:
        """Get cached response if exists"""
        cache_key = self._generate_cache_key(message, pdf_content)
        cached = await self.redis.get(f"{self.cache_prefix}{cache_key}")
        if cached:
            try:
                cached_data = json.loads(cached)
                # Check if cache is still relevant
                if self._is_response_valid(cached_data):
                    return cached_data['response']
            except json.JSONDecodeError:
                return None
        return None

    async def cache_response(self, message: str, pdf_content: str, response: str) -> None:
        """Cache Claude's response"""
        cache_key = self._generate_cache_key(message, pdf_content)
        cache_data = {
            'response': response,
            'timestamp': datetime.utcnow().isoformat(),
            'message': message,
            'pdf_hash': hashlib.sha256(pdf_content.encode()).hexdigest()
        }
        await self.redis.set(
            f"{self.cache_prefix}{cache_key}",
            json.dumps(cache_data),
            expire=self.cache_ttl
        )

    def _generate_cache_key(self, message: str, pdf_content: str) -> str:
        """Generate unique cache key"""
        combined = f"{message.lower().strip()}{hashlib.sha256(pdf_content.encode()).hexdigest()}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def _is_response_valid(self, cached_data: Dict) -> bool:
        """Check if cached response is still valid"""
        cache_time = datetime.fromisoformat(cached_data['timestamp'])
        age = (datetime.utcnow() - cache_time).total_seconds()
        return age < self.cache_ttl