# app/core/config_utils.py
from functools import lru_cache
from typing import Dict, Any
from .config import Settings

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    This function caches the settings to avoid reading environment variables repeatedly.
    """
    return Settings()

def get_db_config() -> Dict[str, Any]:
    """
    Get database configuration dictionary.
    """
    settings = get_settings()
    return {
        "user": settings.ORACLE_USER,
        "password": settings.ORACLE_PASSWORD,
        "dsn": settings.ORACLE_DSN
    }

def get_redis_config() -> Dict[str, Any]:
    """
    Get Redis configuration dictionary.
    """
    settings = get_settings()
    return {
        "host": settings.REDIS_HOST,
        "port": settings.REDIS_PORT,
        "db": settings.REDIS_DB
    }
