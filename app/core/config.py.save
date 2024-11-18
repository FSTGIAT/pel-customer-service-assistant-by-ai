# app/core/config.py
import os
from dotenv import load_dotenv  # correct
# Load .env file
load_dotenv()

class Settings:
    """
    Application settings.
    These values are loaded from environment variables or .env file.
    """
    # Basic API Settings
    API_V1_STR = "/api/v1"
    PROJECT_NAME = "Telecom Customer Service"
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    # Security Settings
    SECRET_KEY = os.getenv("SECRET_KEY")
    
    # Claude API Settings
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    
    # Oracle Database Settings
    ORACLE_USER = os.getenv("ORACLE_USER")
    ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD")
    ORACLE_DSN = os.getenv("ORACLE_DSN")
    
    # Redis Settings
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Create settings instance
settings = Settings()
