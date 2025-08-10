"""Logging middleware for request/response tracking."""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.logging_config import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""

    def __init__(self, app: ASGIApp, skip_paths: list[str] = None):
        """
        Initialize the logging middleware.

        Args:
            app: The ASGI application
            skip_paths: List of paths to skip logging (e.g., /health)
        """
        super().__init__(app)
        self.skip_paths = skip_paths or ["/health", "/metrics"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and response, adding logging.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            The response from the application
        """
        # Skip logging for certain paths
        if request.url.path in self.skip_paths:
            return await call_next(request)

        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        # Start timing
        start_time = time.time()

        # Log request
        logger.info(
            "Request started",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.url.query),
                "client_host": request.client.host if request.client else None,
            },
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            # Log response
            logger.info(
                "Request completed",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )

            return response

        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log error
            logger.error(
                f"Request failed: {str(e)}",
                exc_info=True,
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                },
            )

            # Re-raise the exception
            raise


def get_correlation_id(request: Request) -> str:
    """
    Get the correlation ID from the request.

    Args:
        request: The FastAPI request object

    Returns:
        The correlation ID or "unknown" if not found
    """
    return getattr(request.state, "correlation_id", "unknown")
