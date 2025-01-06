from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.services.session import SessionManager, SessionMiddleware
from app.api.routes import customer, chat, legacy_trigger
from app.core.database import db
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.jobs.cleanup import setup_cleanup_jobs
from app.services.rate_limiting.service import rate_limit_service
from app.services.claude_service import create_claude_service
import logging
from app.api.routes import websocket

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
session_manager = None
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    global session_manager
    try:
        # Startup
        logger.info("Starting up server...")
        
        # Initialize PostgreSQL
        logger.info("Connecting to PostgreSQL...")
        await db.connect()
        logger.info("Successfully connected to PostgreSQL")
        
        # Initialize session manager
        session_manager = SessionManager()
        
        # Test Redis connection
        is_healthy = await session_manager.check_health()
        if not is_healthy:
            raise Exception("Redis health check failed")
        logger.info("Successfully connected to Redis")
        
        # Initialize and start scheduler
        if session_manager:
            logger.info("Setting up cleanup jobs...")
            setup_cleanup_jobs(scheduler)
            scheduler.start()
            logger.info("Cleanup scheduler started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down server...")
        
        # Stop scheduler if running
        if scheduler.running:
            logger.info("Shutting down scheduler...")
            scheduler.shutdown()
        
        # Close Redis connection
        if session_manager:
            await session_manager.close()
            logger.info("Closed Redis connection")
        
        # Close PostgreSQL connection
        await db.disconnect()
        logger.info("Closed PostgreSQL connection")

# Create FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware setup
@app.on_event("startup")
async def startup_event():
    """Add session middleware after session manager is initialized."""
    global session_manager
    if session_manager:
        app.add_middleware(SessionMiddleware, session_manager=session_manager)
    else:
        logger.error("Session manager not initialized")

# Health check endpoint
@app.get("/health")
async def health_check():
    db_healthy = False
    redis_healthy = False
    scheduler_healthy = scheduler.running
    
    try:
        # Check PostgreSQL
        async with db.connection() as conn:
            await conn.fetchval('SELECT 1')
            db_healthy = True
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {str(e)}")

    try:
        # Check Redis
        redis_healthy = await session_manager.check_health()
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")

    return {
        "status": "healthy" if (db_healthy and redis_healthy and scheduler_healthy) else "unhealthy",
        "postgresql": "up" if db_healthy else "down",
        "redis": "up" if redis_healthy else "down",
        "scheduler": "up" if scheduler_healthy else "down"
    }

@asynccontextmanager
async def lifespan(app: FastAPI):
    claude_service = create_claude_service(rate_limit_service)
    queue_processor = asyncio.create_task(
        rate_limit_service.process_claude_queue()
    )
    try:
        yield
    finally:
        queue_processor.cancel()

# Include routers
app.include_router(customer.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(legacy_trigger.router, prefix="/api")
app.include_router(websocket.router)

@app.get("/")
async def root():
    return {"message": "Pelephone Customer Service API"}
