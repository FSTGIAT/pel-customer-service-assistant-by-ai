# app/core/config_validation.py
from .config import settings
import sys

def validate_config():
    """
    Validate that all required configuration values are set.
    Exits the application if any required values are missing.
    """
    required_settings = {
        "SECRET_KEY": settings.SECRET_KEY,
        "ANTHROPIC_API_KEY": settings.ANTHROPIC_API_KEY,
        "ORACLE_USER": settings.ORACLE_USER,
        "ORACLE_PASSWORD": settings.ORACLE_PASSWORD,
        "ORACLE_DSN": settings.ORACLE_DSN
    }

    missing_settings = []
    for key, value in required_settings.items():
        if not value:
            missing_settings.append(key)

    if missing_settings:
        print("Error: Missing required configuration values:")
        for setting in missing_settings:
            print(f"- {setting}")
        sys.exit(1)

    print("Configuration validation successful!")
