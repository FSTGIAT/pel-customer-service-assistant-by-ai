# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Settings
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Pelephone Customer Service"
    
    # Security
    SECRET_KEY: str
    
    # Claude API
    ANTHROPIC_API_KEY: str
    
    # Oracle Database
    ORACLE_USER: str
    ORACLE_PASSWORD: str
    ORACLE_DSN: str
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # PostgreSQL Configuration
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "telecom_user"
    DB_PASSWORD: str
    DB_NAME: str = "telecom_qa"
    
    # Database connection settings
    DB_POOL_MIN_SIZE: int = 10
    DB_POOL_MAX_SIZE: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()