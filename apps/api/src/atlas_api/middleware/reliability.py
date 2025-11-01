"""
Reliability middleware for FastAPI.

Implements DDIA Chapter 1 patterns:
- Request timeouts
- Error handling and structured logging
- Request ID tracking for distributed tracing
- Rate limiting and load shedding

Reference: DDIA Chapter 1 - Reliability, Scalability
"""

import asyncio
import logging
import time
import uuid
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from atlas_api.config import get_settings
from atlas_api.instrumentation.metrics import (
    http_request_duration_seconds,
    http_requests_in_progress,
    http_requests_total,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add request ID for distributed tracing.

    DDIA Chapter 1: Request IDs are essential for tracing requests
    through a distributed system. They enable correlation of logs
    and metrics across services.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Add request ID to request and response.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response with request ID header
        """
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Store in request state for access in handlers
        request.state.request_id = request_id

        # Call next middleware/handler
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response


class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce request timeouts.

    DDIA Chapter 1: Timeouts are critical for preventing resource exhaustion.
    Without timeouts, a slow upstream service can cause cascading failures.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Enforce timeout on request.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response or 504 Gateway Timeout if timeout exceeded
        """
        try:
            # Use configured timeout
            timeout = settings.http_timeout

            response = await asyncio.wait_for(call_next(request), timeout=timeout)
            return response

        except asyncio.TimeoutError:
            logger.warning(
                f"Request timeout after {settings.http_timeout}s",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "request_id": getattr(request.state, "request_id", None),
                },
            )

            return JSONResponse(
                status_code=504,
                content={
                    "error": "Gateway Timeout",
                    "message": f"Request exceeded {settings.http_timeout}s timeout",
                    "request_id": getattr(request.state, "request_id", None),
                },
            )


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect HTTP metrics.

    DDIA Chapter 1: Metrics are essential for understanding system behavior.
    This middleware collects RED metrics (Rate, Errors, Duration).
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Collect metrics for request.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response with metrics recorded
        """
        # Normalize endpoint path (remove IDs, etc.)
        endpoint = self._normalize_path(request.url.path)
        method = request.method

        # Track in-progress requests
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

        start_time = time.time()

        try:
            response = await call_next(request)
            status = response.status_code
        except Exception as e:
            # Record error
            http_requests_total.labels(
                method=method, endpoint=endpoint, status="error"
            ).inc()
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()

            logger.error(
                f"Request failed: {type(e).__name__}",
                extra={
                    "path": request.url.path,
                    "method": method,
                    "request_id": getattr(request.state, "request_id", None),
                },
                exc_info=e,
            )
            raise

        finally:
            # Record metrics
            duration = time.time() - start_time

            http_requests_total.labels(
                method=method, endpoint=endpoint, status=status
            ).inc()

            http_request_duration_seconds.labels(
                method=method, endpoint=endpoint
            ).observe(duration)

            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()

        return response

    @staticmethod
    def _normalize_path(path: str) -> str:
        """
        Normalize path for metrics.

        Removes IDs and other variable parts to avoid cardinality explosion.

        Args:
            path: Request path

        Returns:
            Normalized path
        """
        # Remove trailing slashes
        path = path.rstrip("/")

        # Replace UUIDs and numeric IDs with placeholders
        import re

        # UUID pattern
        path = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "{id}",
            path,
            flags=re.IGNORECASE,
        )

        # Numeric IDs
        path = re.sub(r"/\d+", "/{id}", path)

        return path or "/"


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured error handling and logging.

    DDIA Chapter 1: Proper error handling is critical for reliability.
    This middleware ensures all errors are logged with full context.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Handle errors with structured logging.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response or error response
        """
        try:
            response = await call_next(request)
            return response

        except Exception as exc:
            # Log with full context
            logger.error(
                f"Unhandled exception: {type(exc).__name__}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "query_params": dict(request.query_params),
                    "request_id": getattr(request.state, "request_id", None),
                    "client_host": request.client.host if request.client else None,
                },
                exc_info=exc,
            )

            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": str(exc) if settings.debug else "An error occurred",
                    "request_id": getattr(request.state, "request_id", None),
                },
            )


class LoadSheddingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for load shedding under high load.

    DDIA Chapter 1: Load shedding is a critical pattern for preventing
    cascading failures. When the system is overloaded, reject requests
    early to preserve resources for critical operations.
    """

    def __init__(self, app, max_concurrent_requests: int = 1000):
        """
        Initialize load shedding middleware.

        Args:
            app: FastAPI app
            max_concurrent_requests: Maximum concurrent requests
        """
        super().__init__(app)
        self.max_concurrent_requests = max_concurrent_requests
        self.current_requests = 0

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Shed load if too many concurrent requests.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response or 429 Too Many Requests
        """
        if self.current_requests >= self.max_concurrent_requests:
            logger.warning(
                f"Load shedding: rejecting request, {self.current_requests} concurrent requests"
            )

            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": "Server is overloaded, please retry later",
                    "request_id": getattr(request.state, "request_id", None),
                },
            )

        self.current_requests += 1

        try:
            response = await call_next(request)
            return response
        finally:
            self.current_requests -= 1

