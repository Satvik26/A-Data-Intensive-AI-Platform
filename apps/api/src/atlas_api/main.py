"""
Atlas API - Main application entry point.

This module initializes the FastAPI application with all middleware,
routers, and lifecycle event handlers. It implements DDIA-aligned
reliability patterns including graceful shutdown and health checks.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from atlas_api.config import get_settings
from atlas_api.instrumentation.logging import setup_logging
from atlas_api.instrumentation.metrics import setup_metrics
from atlas_api.instrumentation.tracing import setup_tracing
from atlas_api.routers import health

# Initialize settings and logging
settings = get_settings()
setup_logging(settings)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events with proper resource management.
    Implements graceful shutdown pattern from DDIA Chapter 1.

    Args:
        app: FastAPI application instance

    Yields:
        None: Control during application runtime
    """
    # Startup
    logger.info(
        "Starting Atlas API",
        extra={
            "version": settings.app_version,
            "environment": settings.environment,
            "debug": settings.debug,
        },
    )

    # Initialize observability
    if settings.prometheus_enabled:
        setup_metrics()
        logger.info("Prometheus metrics initialized")

    if settings.otel_enabled:
        setup_tracing(settings)
        logger.info("OpenTelemetry tracing initialized")

    # TODO: Initialize database connection pool
    # TODO: Initialize Redis connection pool
    # TODO: Initialize Kafka producer/consumer
    # TODO: Initialize MinIO client
    # TODO: Run database migrations check
    # TODO: Warm up caches

    logger.info("Atlas API startup complete")

    yield

    # Shutdown
    logger.info("Shutting down Atlas API gracefully")

    # TODO: Close database connections
    # TODO: Close Redis connections
    # TODO: Flush Kafka producer
    # TODO: Close MinIO client
    # TODO: Flush metrics
    # TODO: Flush traces

    logger.info("Atlas API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Atlas API",
    description=(
        "Production-grade, DDIA-aligned data-intensive application platform. "
        "Demonstrates reliability, scalability, and maintainability patterns "
        "from 'Designing Data-Intensive Applications'."
    ),
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    debug=settings.debug,
)

# Add CORS middleware
# DDIA: Allow controlled cross-origin access for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Remaining"],
)

# Add GZip middleware for response compression
# DDIA: Reduce network bandwidth usage
app.add_middleware(GZipMiddleware, minimum_size=1000)

# TODO: Add request ID middleware for distributed tracing
# TODO: Add rate limiting middleware
# TODO: Add authentication middleware
# TODO: Add request logging middleware

# Include routers
app.include_router(health.router, tags=["Health"])

# TODO: Include additional routers
# app.include_router(users.router, prefix=f"{settings.api_prefix}/users", tags=["Users"])
# app.include_router(events.router, prefix=f"{settings.api_prefix}/events", tags=["Events"])

# Mount Prometheus metrics endpoint
# Separate ASGI app to avoid middleware interference
if settings.prometheus_enabled:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    """
    Root endpoint.

    Returns basic API information and links to documentation.

    Returns:
        dict: API information
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """
    Global exception handler.

    Catches unhandled exceptions and returns structured error response.
    Logs errors with full context for debugging.

    Args:
        request: FastAPI request object
        exc: Exception that was raised

    Returns:
        JSONResponse: Structured error response
    """
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        extra={
            "path": request.url.path,
            "method": request.method,
            "client": request.client.host if request.client else None,
        },
    )

    # Don't expose internal errors in production
    if settings.is_production:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred",
            },
        )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "type": type(exc).__name__,
        },
    )


if __name__ == "__main__":
    import uvicorn

    # Run with uvicorn for development
    # In production, use gunicorn with uvicorn workers
    uvicorn.run(
        "atlas_api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
        access_log=True,
    )

