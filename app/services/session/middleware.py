from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from .manager import SessionManager

class SessionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, session_manager: SessionManager):
        super().__init__(app)
        self.session_manager = session_manager

    async def dispatch(self, request: Request, call_next):
        request.state.session = self.session_manager
        response = await call_next(request)
        return response