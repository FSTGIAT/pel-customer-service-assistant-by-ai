# app/core/database.py
from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator, Any 
import asyncpg
from fastapi import FastAPI
from app.core.config import settings  # You'll need to create this

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.pool = None
        self._config = {
            'host': settings.DB_HOST,
            'port': settings.DB_PORT,
            'user': settings.DB_USER,
            'password': settings.DB_PASSWORD,
            'database': settings.DB_NAME,
            'min_size': settings.DB_POOL_MIN_SIZE,
            'max_size': settings.DB_POOL_MAX_SIZE,
        }
        logger.info(f"Initializing DatabaseManager with host: {settings.DB_HOST}")


    async def connect(self) -> None:
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(**self._config)
            logger.info("Database connection pool created")
            
            # Test connection
            async with self.pool.acquire() as conn:
                version = await conn.fetchval('SELECT version()')
                logger.info(f"Connected to PostgreSQL: {version}")
                
        except Exception as e:
            logger.error(f"Failed to create database pool: {str(e)}")
            raise

    async def disconnect(self) -> None:
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Get a database connection from the pool"""
        if not self.pool:
            raise RuntimeError("Database not initialized")
            
        async with self.pool.acquire() as conn:
            try:
                yield conn
            except Exception as e:
                await conn.execute('ROLLBACK')
                logger.error(f"Database error: {str(e)}")
                raise

    async def fetch_one(self, query: str, *args) -> dict:
        """Fetch a single row"""
        async with self.connection() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None

    async def fetch_all(self, query: str, *args) -> list:
        """Fetch multiple rows"""
        async with self.connection() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def fetch_val(self, query: str, *args) -> Any:
        """Fetch a single value"""
        async with self.connection() as conn:
            return await conn.fetchval(query, *args)
            
    async def execute(self, query: str, *args) -> str:
        """Execute a query"""
        async with self.connection() as conn:
            return await conn.execute(query, *args)

            
# Global instance
db = DatabaseManager()

# FastAPI lifecycle events
async def connect_to_db(app: FastAPI) -> None:
    await db.connect()

async def close_db_connection(app: FastAPI) -> None:
    await db.disconnect()