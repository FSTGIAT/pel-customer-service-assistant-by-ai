# app/services/session/store.py
from redis import Redis
from app.core.config.session_config import SessionConfig

class SessionStore:
    def __init__(self, config: SessionConfig):
        self.redis = Redis(
            host="localhost",
            port=config.REDIS_SESSION_PORT,
            db=config.REDIS_SESSION_DB,
            decode_responses=True
        )
    
    async def set_session(self, session_id: str, data: dict, expire: int = 300):
        return self.redis.setex(f"session:{session_id}", expire, str(data))

    async def get_session(self, session_id: str):
        return self.redis.get(f"session:{session_id}")