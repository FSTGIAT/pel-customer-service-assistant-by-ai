# app/core/config/session_config.py
from pydantic import BaseSettings

class SessionConfig(BaseSettings):
    REDIS_SESSION_PORT: int = 6380
    REDIS_SESSION_DB: int = 1
    REDIS_SESSION_HOST: str = "localhost"
    SESSION_TIMEOUT: int = 300
    MAX_SESSIONS: int = 1000

    class Config:
        env_prefix = "SESSION_"
        case_sensitive = False

# Create config instance
config = SessionConfig()