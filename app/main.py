from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.services.session import SessionManager, SessionMiddleware
from app.api.routes import customer, chat, legacy_trigger
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global session manager instance
session_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    global session_manager
    logger.info("Starting up server...")
    try:
        session_manager = SessionManager()
        # Test Redis connection
        is_healthy = await session_manager.check_health()
        if not is_healthy:
            raise Exception("Redis health check failed")
        logger.info("Successfully connected to Redis")
        yield
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down server...")
        if session_manager:
            await session_manager.close()
            logger.info("Closed Redis connection")

# Create FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

# CORS middleware first
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware - using the global session_manager
@app.on_event("startup")
async def startup_event():
    """Add session middleware after session manager is initialized."""
    global session_manager
    if session_manager:
        app.add_middleware(SessionMiddleware, session_manager=session_manager)
    else:
        logger.error("Session manager not initialized")

# Include routers
app.include_router(customer.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(legacy_trigger.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Pelephone Customer Service API"}