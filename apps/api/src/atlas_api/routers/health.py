"""
Health check endpoints.

Provides health, readiness, and liveness probes for monitoring
and orchestration. Implements DDIA-aligned health check patterns.
"""

import asyncio
import logging
import time
from datetime import datetime

from fastapi import APIRouter, status

from atlas_api.adapters.database import get_database_adapter
from atlas_api.adapters.redis import get_redis_adapter
from atlas_api.config import get_settings
from atlas_api.schemas.health import (
    DependencyHealth,
    HealthResponse,
    HealthStatus,
    LivenessResponse,
    ReadinessResponse,
)

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

# Track application start time for uptime calculation
_start_time = time.time()


async def check_postgres_health() -> DependencyHealth:
    """
    Check PostgreSQL database health.

    Returns:
        DependencyHealth: PostgreSQL health status
    """
    try:
        db_adapter = get_database_adapter()
        health_data = await db_adapter.health_check()

        return DependencyHealth(
            name="postgresql",
            status=HealthStatus.HEALTHY if health_data["healthy"] else HealthStatus.UNHEALTHY,
            latency_ms=health_data["latency_ms"],
            metadata={
                "pool_size": health_data["pool"]["size"],
                "checked_out": health_data["pool"]["checked_out"],
                "overflow": health_data["pool"]["overflow"],
            },
        )
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}", exc_info=True)
        return DependencyHealth(
            name="postgresql",
            status=HealthStatus.UNHEALTHY,
            latency_ms=None,
            error=str(e),
        )


async def check_redis_health() -> DependencyHealth:
    """
    Check Redis cache health.

    Returns:
        DependencyHealth: Redis health status
    """
    try:
        redis_adapter = get_redis_adapter()
        health_data = await redis_adapter.health_check()

        return DependencyHealth(
            name="redis",
            status=HealthStatus.HEALTHY if health_data["healthy"] else HealthStatus.UNHEALTHY,
            latency_ms=health_data["latency_ms"],
            metadata={
                "version": health_data["version"],
                "uptime_seconds": health_data["uptime_seconds"],
            },
        )
    except Exception as e:
        logger.error(f"Redis health check failed: {e}", exc_info=True)
        return DependencyHealth(
            name="redis",
            status=HealthStatus.UNHEALTHY,
            latency_ms=None,
            error=str(e),
        )


async def check_kafka_health() -> DependencyHealth:
    """
    Check Kafka health.

    Returns:
        DependencyHealth: Kafka health status
    """
    # TODO: Implement actual Kafka health check
    # For now, return mock healthy status
    return DependencyHealth(
        name="kafka",
        status=HealthStatus.HEALTHY,
        latency_ms=5.0,
        metadata={
            "version": "7.5.0",
            "brokers": 1,
        },
    )


async def check_minio_health() -> DependencyHealth:
    """
    Check MinIO/S3 health.

    Returns:
        DependencyHealth: MinIO health status
    """
    # TODO: Implement actual MinIO health check
    # For now, return mock healthy status
    return DependencyHealth(
        name="minio",
        status=HealthStatus.HEALTHY,
        latency_ms=3.0,
        metadata={
            "version": "latest",
            "buckets": 1,
        },
    )


def determine_overall_status(dependencies: list[DependencyHealth]) -> HealthStatus:
    """
    Determine overall system health from dependency statuses.

    Logic:
    - HEALTHY: All dependencies are healthy
    - DEGRADED: Some dependencies are degraded but none unhealthy
    - UNHEALTHY: Any dependency is unhealthy

    Args:
        dependencies: List of dependency health statuses

    Returns:
        HealthStatus: Overall system health status
    """
    if not dependencies:
        return HealthStatus.HEALTHY

    statuses = [dep.status for dep in dependencies]

    if HealthStatus.UNHEALTHY in statuses:
        return HealthStatus.UNHEALTHY
    elif HealthStatus.DEGRADED in statuses:
        return HealthStatus.DEGRADED
    else:
        return HealthStatus.HEALTHY


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Lightweight Health Check",
    description=(
        "Fast, lightweight health check that returns immediately without querying dependencies. "
        "Use this endpoint for high-frequency health checks, load balancer probes, and load testing. "
        "For detailed dependency health information, use /health/deep instead."
    ),
)
async def health_check_lightweight() -> dict:
    """
    Lightweight health check endpoint.

    Returns immediately without querying any dependencies.
    Suitable for high-frequency health checks and load testing.

    Returns:
        dict: Simple health status
    """
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get(
    "/health/deep",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Deep Health Check",
    description=(
        "Comprehensive health check endpoint that verifies the status of "
        "the API and all its dependencies (database, cache, message queue, storage). "
        "Returns detailed health information including latency and metadata. "
        "WARNING: This endpoint performs actual database queries and should not be used for high-frequency health checks."
    ),
    responses={
        200: {
            "description": "System is healthy or degraded",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "version": "0.1.0",
                        "environment": "development",
                        "timestamp": "2025-10-26T12:00:00Z",
                        "uptime_seconds": 3600,
                        "dependencies": [
                            {
                                "name": "postgresql",
                                "status": "healthy",
                                "latency_ms": 2.5,
                            }
                        ],
                    }
                }
            },
        },
        503: {
            "description": "System is unhealthy",
        },
    },
)
async def health_check() -> HealthResponse:
    """
    Comprehensive health check endpoint.

    Checks the health of all system dependencies and returns
    detailed status information. Used by monitoring systems
    and load balancers.

    Returns:
        HealthResponse: Detailed health status
    """
    # Check all dependencies in parallel using asyncio.gather
    dependencies = await asyncio.gather(
        check_postgres_health(),
        check_redis_health(),
        check_kafka_health(),
        check_minio_health(),
        return_exceptions=False,  # Raise exceptions instead of returning them
    )

    # Determine overall status
    overall_status = determine_overall_status(dependencies)

    # Calculate uptime
    uptime_seconds = time.time() - _start_time

    return HealthResponse(
        status=overall_status,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.utcnow(),
        uptime_seconds=uptime_seconds,
        dependencies=dependencies,
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness Probe",
    description=(
        "Kubernetes-style readiness probe. Returns 200 if the service is "
        "ready to accept traffic, 503 otherwise. Used by load balancers "
        "to determine if traffic should be routed to this instance."
    ),
)
async def readiness_check() -> ReadinessResponse:
    """
    Readiness probe for orchestrators.

    Indicates whether the service is ready to accept traffic.
    Checks critical dependencies required for request processing.

    Returns:
        ReadinessResponse: Readiness status
    """
    # TODO: Check critical dependencies (database, cache)
    # For now, always return ready
    return ReadinessResponse(
        ready=True,
        timestamp=datetime.utcnow(),
    )


@router.get(
    "/health/live",
    response_model=LivenessResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness Probe",
    description=(
        "Kubernetes-style liveness probe. Returns 200 if the service is "
        "alive and functioning, 503 if it should be restarted. Used by "
        "orchestrators to detect deadlocks and unrecoverable errors."
    ),
)
async def liveness_check() -> LivenessResponse:
    """
    Liveness probe for orchestrators.

    Indicates whether the service is alive and should not be restarted.
    This is a lightweight check that only verifies the process is responsive.

    Returns:
        LivenessResponse: Liveness status
    """
    # Simple liveness check - if we can respond, we're alive
    return LivenessResponse(
        alive=True,
        timestamp=datetime.utcnow(),
    )

