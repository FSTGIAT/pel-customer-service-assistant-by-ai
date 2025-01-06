# app/services/session/manager.py
import uuid
from datetime import datetime
import redis
import logging
import json

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self):
        self.redis = redis.Redis(
            host="localhost",
            port=6380,
            db=1,
            decode_responses=True
        )


    async def check_health(self) -> bool:
        try:
            return self.redis.ping()
        except:
            return False

    # Add this new method
    async def close(self):
        """Close Redis connection"""
        try:
            self.redis.close()
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
        
    async def create_session(self, customer_id: str) -> dict:
        try:
            session_id = str(uuid.uuid4())
            session_data = {
                "id": session_id,
                "customer_id": customer_id,
                "created_at": datetime.utcnow().isoformat(),
                "last_active": datetime.utcnow().isoformat()
            }
            
            # Store in Redis with 5-minute timeout
            self.redis.setex(
                f"session:{session_id}",
                300,  # 5 minutes
                json.dumps(session_data)
            )
            
            logger.info(f"Created session: {session_data}")
            return session_data
            
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            raise

    async def get_session(self, session_id: str) -> dict:
        """Get session data by ID"""
        try:
            data = self.redis.get(f"session:{session_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {str(e)}")
            return None

    async def get_active_session(self, customer_id: str) -> dict:
        """Get active session for customer"""
        try:
            # Get all session keys
            session_keys = self.redis.keys("session:*")
            
            for key in session_keys:
                session_data = self.redis.get(key)
                if session_data:
                    session = json.loads(session_data)
                    if session["customer_id"] == customer_id:
                        return session
            return None
        except Exception as e:
            logger.error(f"Error getting active session: {str(e)}")
            return None

    async def update_session_activity(self, session_id: str):
        """Update session last activity time"""
        try:
            session_data = await self.get_session(session_id)
            if session_data:
                session_data["last_active"] = datetime.utcnow().isoformat()
                self.redis.setex(
                    f"session:{session_id}",
                    300,  # Reset 5-minute timeout
                    json.dumps(session_data)
                )
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating session activity: {str(e)}")
            return False

    async def delete_session(self, session_id: str):
        """Delete a session"""
        try:
            return self.redis.delete(f"session:{session_id}")
        except Exception as e:
            logger.error(f"Error deleting session: {str(e)}")
            return False

    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            # Redis automatically removes expired keys
            return True
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {str(e)}")
            return False

    async def check_health(self) -> bool:
        """Check if session service is healthy"""
        try:
            return self.redis.ping()
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False