"""
Health check schemas.

Defines request/response models for health check endpoints.
Implements DDIA-aligned health check patterns for monitoring.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class HealthStatus(str, Enum):
    """Health check status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class DependencyHealth(BaseModel):
    """
    Health status of a single dependency.

    Tracks the health of external dependencies like databases,
    caches, and message queues.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "postgresql",
                "status": "healthy",
                "latency_ms": 2.5,
                "error": None,
            }
        }
    )

    name: str = Field(..., description="Dependency name (e.g., 'postgresql', 'redis')")
    status: HealthStatus = Field(..., description="Current health status")
    latency_ms: float | None = Field(
        None,
        description="Response latency in milliseconds",
        ge=0,
    )
    error: str | None = Field(None, description="Error message if unhealthy")
    metadata: dict[str, str | int | float] | None = Field(
        None,
        description="Additional metadata (e.g., version, connection count)",
    )


class HealthResponse(BaseModel):
    """
    Overall system health response.

    Aggregates health status from all dependencies and provides
    overall system health assessment.
    """

    model_config = ConfigDict(
        json_schema_extra={
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
                        "metadata": {"version": "15.0", "connections": 5},
                    },
                    {
                        "name": "redis",
                        "status": "healthy",
                        "latency_ms": 1.2,
                        "metadata": {"version": "7.0", "memory_mb": 128},
                    },
                ],
            }
        }
    )

    status: HealthStatus = Field(..., description="Overall system health status")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Deployment environment")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Health check timestamp (UTC)",
    )
    uptime_seconds: float = Field(..., description="Application uptime in seconds", ge=0)
    dependencies: list[DependencyHealth] = Field(
        default_factory=list,
        description="Health status of all dependencies",
    )


class ReadinessResponse(BaseModel):
    """
    Readiness probe response.

    Indicates whether the service is ready to accept traffic.
    Used by load balancers and orchestrators (K8s).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ready": True,
                "timestamp": "2025-10-26T12:00:00Z",
            }
        }
    )

    ready: bool = Field(..., description="Whether service is ready to accept traffic")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Check timestamp (UTC)",
    )


class LivenessResponse(BaseModel):
    """
    Liveness probe response.

    Indicates whether the service is alive and should not be restarted.
    Used by orchestrators (K8s) to detect deadlocks.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "alive": True,
                "timestamp": "2025-10-26T12:00:00Z",
            }
        }
    )

    alive: bool = Field(..., description="Whether service is alive")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Check timestamp (UTC)",
    )

