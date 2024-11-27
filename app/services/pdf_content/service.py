from typing import Optional, List, Dict
from datetime import datetime
import hashlib
import json

class PDFContentService:
    def __init__(self, db, redis_client):
        self.db = db
        self.redis = redis_client
        self.cache_ttl = 3600  # 1 hour

    async def get_relevant_content(self, message: str, pdf_paths: List[str]) -> str:
        """Get relevant PDF content based on user query"""
        try:
            # Generate content hash for the combination
            content_hash = self._generate_content_hash(message, pdf_paths)
            
            # Try Redis first
            cached_content = await self.redis.get(f"pdf_content:{content_hash}")
            if cached_content:
                return json.loads(cached_content)

            # Get from database
            query = """
                SELECT content 
                FROM telecom.pdf_content_cache 
                WHERE content_hash = ANY($1)
                ORDER BY created_at DESC
            """
            
            results = await self.db.fetch_all(query, pdf_paths)
            
            # Combine and process content
            combined_content = ""
            for result in results:
                content = result['content']
                # Add only relevant sections based on message keywords
                if self._is_content_relevant(message, content):
                    combined_content += f"\n{content}"

            # Cache the processed content
            await self.redis.set(
                f"pdf_content:{content_hash}",
                json.dumps(combined_content),
                expire=self.cache_ttl
            )

            return combined_content

    def _generate_content_hash(self, message: str, pdf_paths: List[str]) -> str:
        """Generate hash for content caching"""
        content = f"{message}{''.join(sorted(pdf_paths))}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _is_content_relevant(self, message: str, content: str) -> bool:
        """Check if content section is relevant to query"""
        # Extract keywords from message
        keywords = self._extract_keywords(message.lower())
        
        # Check content relevance
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in keywords)

    def _extract_keywords(self, message: str) -> List[str]:
        """Extract keywords from message"""
        # Add common billing keywords
        billing_keywords = ['חשבון', 'תשלום', 'חיוב', 'סכום', 'עלות', 'תעריף']
        message_words = message.split()
        return list(set(message_words + billing_keywords))