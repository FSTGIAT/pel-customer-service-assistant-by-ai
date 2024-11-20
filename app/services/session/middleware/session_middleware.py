from typing import Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from ..manager import SessionManager
import redis
import json
import logging

logger = logging.getLogger(__name__)

class SessionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, session_manager: SessionManager):
        """Initialize middleware with session manager."""
        super().__init__(app)
        self.session_manager = session_manager
        
    async def dispatch(self, request: Request, call_next):
        """Process each request to validate and manage session."""
        try:
            # Extract customer_id from request path or query params
            customer_id = await self._extract_customer_id(request)
            if not customer_id:
                return await call_next(request)

            # Get or create session
            session = await self.session_manager.get_active_session(customer_id)
            if not session:
                session = await self.session_manager.create_session(customer_id)

            # Attach session to request state
            request.state.session = session
            request.state.customer_id = customer_id

            # Process request
            response = await call_next(request)

            # Update session activity
            if session and 'id' in session:
                await self.session_manager.update_session_activity(session['id'])

            return response

        except redis.ConnectionError:
            logger.error("Redis connection failed")
            return JSONResponse(
                status_code=503,
                content={"detail": "Session service unavailable"}
            )
        except Exception as e:
            logger.error(f"Session middleware error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )

    async def _extract_customer_id(self, request: Request) -> Optional[str]:
        """Extract customer_id from request."""
        # Try path parameters first
        customer_id = request.path_params.get('customer_id')
        if customer_id:
            return customer_id

        # Try query parameters
        customer_id = request.query_params.get('customer_id')
        if customer_id:
            return customer_id

        # Try headers
        customer_id = request.headers.get('X-Customer-ID')
        if customer_id:
            return customer_id

        # Try body for POST requests
        if request.method == "POST":
            try:
                body = await request.json()
                if isinstance(body, dict):
                    return body.get('customer_id')
            except:
                pass

        return None