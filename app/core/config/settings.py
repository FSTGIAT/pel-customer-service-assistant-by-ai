from pydantic_settings import BaseSettings

class SessionSettings(BaseSettings):
    REDIS_SESSION_PORT: int = 6380
    REDIS_SESSION_DB: int = 1
    REDIS_SESSION_HOST: str = "localhost"
    SESSION_TIMEOUT: int = 300
    MAX_SESSIONS: int = 1000

    class Config:
        env_prefix = "SESSION_"
        case_sensitive = False

session_settings = SessionSettings()

# Export SessionSettings
Settings = SessionSettings  # This line fixes the import issue
settings = session_settings  # This provides the expected settings import

__all__ = ['Settings', 'settings', 'SessionSettings', 'session_settings']