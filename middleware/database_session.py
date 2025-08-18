"""
Database Session Management Middleware
Ensures proper database connection lifecycle and graceful shutdown
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from sqlalchemy.exc import OperationalError
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from config.settings import settings
import time


class DatabaseSessionMiddleware(BaseHTTPMiddleware):
    """
    Middleware for production-grade database session management
    Handles connection pooling, timeouts, and graceful degradation
    """

    def __init__(self, app):
        super().__init__(app)
        self.engine = None
        self._setup_engine()

    def _setup_engine(self):
        """Setup SQLAlchemy engine with production settings"""
        if settings.database_url:
            # Production database configuration
            engine_kwargs = {
                "pool_pre_ping": True,  # Validate connections before use
                "pool_recycle": 280,    # Recycle connections every ~5 minutes  
                "pool_size": 5,         # Connection pool size
                "max_overflow": 10,     # Additional connections beyond pool_size
                "echo": settings.is_development,  # SQL logging in development only
            }
            
            # Add connection timeouts for PostgreSQL
            if "postgresql" in settings.database_url:
                engine_kwargs["connect_args"] = {
                    "connect_timeout": 10,
                    "application_name": "scholarship_api"
                }
            
            self.engine = create_engine(settings.database_url, **engine_kwargs)

    async def dispatch(self, request: Request, call_next):
        """Handle request with database session management"""
        
        # Store engine in request state for health checks
        if self.engine:
            request.state.db_engine = self.engine
        
        try:
            response = await call_next(request)
            return response
        except OperationalError as e:
            # Database connection error - return 503 with unified format
            from fastapi import HTTPException
            
            error_detail = {
                "trace_id": getattr(request.state, 'trace_id', 'db_error'),
                "code": "DATABASE_UNAVAILABLE",
                "message": "Database connection unavailable",
                "status": 503,
                "timestamp": int(time.time())
            }
            
            raise HTTPException(status_code=503, detail=error_detail)

    async def __call__(self, scope, receive, send):
        """ASGI interface with graceful shutdown handling"""
        if scope["type"] == "lifespan":
            # Handle application lifecycle events
            message = await receive()
            if message["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                # Gracefully close database connections
                if self.engine:
                    self.engine.dispose()
                await send({"type": "lifespan.shutdown.complete"})
        else:
            # Regular HTTP request
            await super().__call__(scope, receive, send)