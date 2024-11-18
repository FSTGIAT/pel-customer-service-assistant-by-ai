# test_config.py
from app.core import validate_config, settings

def main():
    # Validate configuration
    validate_config()
    
    # Print current settings
    print("\nCurrent Configuration:")
    print(f"Project Name: {settings.PROJECT_NAME}")
    print(f"API Version: {settings.API_V1_STR}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"Redis Host: {settings.REDIS_HOST}")
    print(f"Redis Port: {settings.REDIS_PORT}")

if __name__ == "__main__":
    main()
