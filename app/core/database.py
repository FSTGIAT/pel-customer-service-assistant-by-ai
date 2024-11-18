# app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import cx_Oracle

# Oracle connection string
ORACLE_URL = f"oracle://{settings.ORACLE_USER}:{settings.ORACLE_PASSWORD}@{settings.ORACLE_DSN}"

# Create engine with connection pooling
engine = create_engine(
    ORACLE_URL,
    max_identifier_length=128,
    pool_size=settings.ORACLE_POOL_SIZE,
    max_overflow=settings.ORACLE_MAX_OVERFLOW
)

# SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for database models
Base = declarative_base()

# Database dependency
def get_db():
    """
    Database session dependency.
    Use this as a FastAPI dependency for routes that need database access.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
