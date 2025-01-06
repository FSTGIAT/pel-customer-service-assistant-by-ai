from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
from app.core.database import db
from .models import ChatMessage, ChatHistoryResponse
import logging
import json
import secrets

logger = logging.getLogger(__name__)

class ChatHistoryService:
    SESSION_EXPIRY_MINUTES = 60 
    @staticmethod
    def generate_session_token() -> str:
        """Generate a secure session token"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def calculate_expiry() -> datetime:
        """Calculate session expiry time"""
        return datetime.utcnow() + timedelta(minutes=ChatHistoryService.SESSION_EXPIRY_MINUTES)

    async def ensure_customer_exists(self, customer_id: str) -> bool:
        """Ensure customer exists in the database"""
        try:
            # First check if customer exists
            check_query = """
                SELECT EXISTS(
                    SELECT 1 FROM telecom.customers 
                    WHERE id = $1
                )
            """
            exists = await db.fetch_one(check_query, customer_id)
            
            if not exists or not exists['exists']:
                # Create customer if doesn't exist
                create_query = """
                    INSERT INTO telecom.customers 
                    (id, created_at, metadata)
                    VALUES ($1, NOW(), $2)
                    ON CONFLICT (id) DO NOTHING
                    RETURNING id
                """
                metadata = {
                    'created_timestamp': datetime.utcnow().isoformat(),
                    'source': 'chat_service'
                }
                await db.execute(create_query, customer_id, json.dumps(metadata))
                logger.info(f"Created new customer record for {customer_id}")
            
            return True
        except Exception as e:
            logger.error(f"Error ensuring customer exists: {e}")
            raise


    async def ensure_session_exists(self, session_id: UUID, customer_id: str) -> bool:
        """Create session if it doesn't exist"""
        try:
            await self.ensure_customer_exists(customer_id)
            check_query = """
                SELECT EXISTS(
                    SELECT 1 FROM telecom.sessions 
                    WHERE id = $1
                )
            """
            exists = await db.fetch_one(check_query, str(session_id))
            
            if not exists or not exists['exists']:
                # Create session
                create_query = """
                    INSERT INTO telecom.sessions 
                    (id, customer_id, session_token, created_at, last_activity, expires_at, metadata)
                    VALUES ($1, $2, $3, NOW(), NOW(), $4, $5)
                    ON CONFLICT (id) DO NOTHING
                    RETURNING id
                """
                session_token = self.generate_session_token()
                expires_at = ChatHistoryService.calculate_expiry()
                metadata = {
                    'created_timestamp': datetime.utcnow().isoformat(),
                    'customer_id': customer_id,
                    'expires_at': expires_at.isoformat()
                }

                await db.execute(
                    create_query, 
                    str(session_id), 
                    customer_id,
                    session_token,
                    expires_at,
                    json.dumps(metadata)
                )
                logger.info(f"Created new session {session_id} with expiry {expires_at}")
                return True
            
            return True
        except Exception as e:
            logger.error(f"Error ensuring session exists: {e}")
            raise

    async def save_message(self, message: ChatMessage) -> UUID:
        """Save a chat message to the database"""
        try:
            customer_id = message.metadata.get('customer_id')
            if not customer_id:
                raise ValueError("customer_id not found in message metadata")

            update_session_query = """
                UPDATE telecom.sessions 
                SET last_activity = NOW(),
                    expires_at = $2
                WHERE id = $1
            """
            new_expiry = ChatHistoryService.calculate_expiry() 
            await db.execute(
                update_session_query,
                str(message.session_id),
                new_expiry
            )

            await self.ensure_session_exists(message.session_id, customer_id)
            query = """
                INSERT INTO telecom.chat_messages 
                (session_id, message_type, content, pdf_context, metadata)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """
            metadata_json = json.dumps(message.metadata)
            message_id = await db.fetch_one(
                query,
                str(message.session_id),
                message.message_type,
                message.content,
                str(message.pdf_context) if message.pdf_context else None,
                metadata_json
            )
            return message_id['id']
        except Exception as e:
            logger.error(f"Error saving chat message: {e}")
            raise

    async def get_session_history(
        self, 
        session_id: UUID, 
        limit: int = 50,
        offset: int = 0
    ) -> ChatHistoryResponse:
        """Get chat history for a session"""
        try:
            # Get messages
            query = """
                SELECT 
                    id, session_id, message_type, content, 
                    created_at, pdf_context, metadata
                FROM telecom.chat_messages
                WHERE session_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
            """
            messages = await db.fetch_all(query, str(session_id), limit, offset)
            
            # Get total count
            count_query = "SELECT COUNT(*) FROM telecom.chat_messages WHERE session_id = $1"
            total = await db.fetch_val(count_query, str(session_id))
            
            return ChatHistoryResponse(
                messages=[ChatMessage(**msg) for msg in messages],
                total_count=total,
                has_more=total > (offset + limit)
            )
        except Exception as e:
            logger.error(f"Error getting session history: {e}")
            raise

    async def get_customer_history(
        self, 
        customer_id: str,
        days: int = 30,
        limit: int = 100,
        offset: int = 0
    ) -> ChatHistoryResponse:
        """Get chat history for a customer across all sessions"""
        try:
            query = """
                SELECT 
                    cm.id, cm.session_id, cm.message_type, cm.content,
                    cm.created_at, cm.pdf_context, cm.metadata
                FROM telecom.chat_messages cm
                JOIN telecom.sessions s ON cm.session_id = s.id
                WHERE s.customer_id = $1
                AND cm.created_at > NOW() - INTERVAL '$2 days'
                ORDER BY cm.created_at DESC
                LIMIT $3 OFFSET $4
            """
            messages = await db.fetch_all(query, customer_id, days, limit, offset)
            
            # Get total count
            count_query = """
                SELECT COUNT(*)
                FROM telecom.chat_messages cm
                JOIN telecom.sessions s ON cm.session_id = s.id
                WHERE s.customer_id = $1
                AND cm.created_at > NOW() - INTERVAL '$2 days'
            """
            total = await db.fetch_val(count_query, customer_id, days)
            
            return ChatHistoryResponse(
                messages=[ChatMessage(**msg) for msg in messages],
                total_count=total,
                has_more=total > (offset + limit)
            )
        except Exception as e:
            logger.error(f"Error getting customer history: {e}")
            raise

    async def cleanup_old_history(self, days: int = 90):
        """Cleanup chat history older than specified days"""
        try:
            await db.execute(
                "SELECT telecom.cleanup_old_chat_messages()"
            )
        except Exception as e:
            logger.error(f"Error cleaning up chat history: {e}")
            raise

chat_history_service = ChatHistoryService()