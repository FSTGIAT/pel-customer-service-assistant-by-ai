from pydantic_settings import BaseSettings

class SessionSettings(BaseSettings):
    REDIS_SESSION_PORT: int = 6380
    REDIS_SESSION_DB: int = 1
    REDIS_SESSION_HOST: str = "localhost"
    SESSION_TIMEOUT: int = 300
    MAX_SESSIONS: int = 1000
    REDIS_TTL: int = 3600

        # Add PostgreSQL settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "telecom_user"
    DB_PASSWORD: str = "telecom123"  # Will be overridden by env var
    DB_NAME: str = "telecom_qa"
    DB_POOL_MIN_SIZE: int = 10
    DB_POOL_MAX_SIZE: int = 30

    # API Settings
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Pelephone Customer Service"
    
    # Claude API settings
    ANTHROPIC_API_KEY: str = ""

    class Config:
        env_prefix = "SESSION_"
        case_sensitive = False

session_settings = SessionSettings()

# Export SessionSettings
Settings = SessionSettings  # This line fixes the import issue
settings = session_settings  # This provides the expected settings import

__all__ = ['Settings', 'settings', 'SessionSettings', 'session_settings']