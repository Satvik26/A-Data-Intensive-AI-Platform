"""
Service Level Indicators (SLIs) and Service Level Objectives (SLOs).

Implements DDIA Chapter 1 principles for defining and monitoring system reliability.
SLIs are measurable metrics, SLOs are targets for those metrics.

Reference: DDIA Chapter 1 - Reliability, Scalability, Maintainability
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SLIType(str, Enum):
    """Types of Service Level Indicators."""

    LATENCY = "latency"  # Response time
    ERROR_RATE = "error_rate"  # Fraction of requests that fail
    THROUGHPUT = "throughput"  # Requests per second
    AVAILABILITY = "availability"  # Fraction of time service is available


@dataclass
class LatencySLI:
    """Latency SLI with percentile targets.

    DDIA Chapter 1: Latency is not the same as response time.
    Latency is the delay to get a response, measured from client perspective.
    """

    p50_ms: float  # Median latency
    p95_ms: float  # 95th percentile
    p99_ms: float  # 99th percentile
    p999_ms: float  # 99.9th percentile

    def __post_init__(self) -> None:
        """Validate percentile ordering."""
        if not (self.p50_ms <= self.p95_ms <= self.p99_ms <= self.p999_ms):
            raise ValueError("Percentiles must be in ascending order")


@dataclass
class ErrorRateSLI:
    """Error rate SLI.

    DDIA Chapter 1: Errors are a key reliability metric.
    Includes both client errors (4xx) and server errors (5xx).
    """

    max_error_rate: float  # Max fraction of requests that can fail (0.0-1.0)
    max_5xx_rate: float  # Max fraction of 5xx errors (0.0-1.0)

    def __post_init__(self) -> None:
        """Validate error rates."""
        if not (0.0 <= self.max_error_rate <= 1.0):
            raise ValueError("Error rate must be between 0.0 and 1.0")
        if not (0.0 <= self.max_5xx_rate <= 1.0):
            raise ValueError("5xx rate must be between 0.0 and 1.0")


@dataclass
class ThroughputSLI:
    """Throughput SLI.

    DDIA Chapter 1: Throughput is requests per second the system can handle.
    """

    min_rps: float  # Minimum requests per second
    max_rps: float  # Maximum requests per second (capacity)

    def __post_init__(self) -> None:
        """Validate throughput."""
        if self.min_rps < 0 or self.max_rps < 0:
            raise ValueError("Throughput must be non-negative")
        if self.min_rps > self.max_rps:
            raise ValueError("Min RPS must be <= max RPS")


@dataclass
class AvailabilitySLI:
    """Availability SLI.

    DDIA Chapter 1: Availability is the fraction of time the service is available.
    """

    min_availability: float  # Minimum availability (0.0-1.0)

    def __post_init__(self) -> None:
        """Validate availability."""
        if not (0.0 <= self.min_availability <= 1.0):
            raise ValueError("Availability must be between 0.0 and 1.0")


@dataclass
class ServiceLevelObjective:
    """Service Level Objective (SLO).

    Combines multiple SLIs into a single objective for a service.
    SLOs are targets that the service should meet.

    DDIA Chapter 1: SLOs are the foundation of reliability engineering.
    They define what "good" looks like for a service.
    """

    name: str
    description: str
    latency: LatencySLI
    error_rate: ErrorRateSLI
    throughput: ThroughputSLI
    availability: AvailabilitySLI
    window_minutes: int = 5  # Evaluation window (5 min, 1 hour, 1 day, etc.)


# Default SLOs for Atlas API
# These are conservative targets suitable for a production system

ATLAS_API_SLO = ServiceLevelObjective(
    name="atlas-api",
    description="Atlas API Service Level Objective",
    latency=LatencySLI(
        p50_ms=50.0,  # Median: 50ms
        p95_ms=200.0,  # 95th percentile: 200ms
        p99_ms=500.0,  # 99th percentile: 500ms
        p999_ms=1000.0,  # 99.9th percentile: 1 second
    ),
    error_rate=ErrorRateSLI(
        max_error_rate=0.01,  # Max 1% error rate
        max_5xx_rate=0.001,  # Max 0.1% 5xx errors
    ),
    throughput=ThroughputSLI(
        min_rps=100.0,  # Minimum 100 RPS
        max_rps=10000.0,  # Maximum 10,000 RPS
    ),
    availability=AvailabilitySLI(
        min_availability=0.999,  # 99.9% availability (3 nines)
    ),
    window_minutes=5,
)

# Stricter SLOs for critical endpoints
CRITICAL_ENDPOINT_SLO = ServiceLevelObjective(
    name="critical-endpoints",
    description="SLO for critical endpoints (auth, payments, etc.)",
    latency=LatencySLI(
        p50_ms=20.0,
        p95_ms=100.0,
        p99_ms=200.0,
        p999_ms=500.0,
    ),
    error_rate=ErrorRateSLI(
        max_error_rate=0.001,  # Max 0.1% error rate
        max_5xx_rate=0.0001,  # Max 0.01% 5xx errors
    ),
    throughput=ThroughputSLI(
        min_rps=50.0,
        max_rps=5000.0,
    ),
    availability=AvailabilitySLI(
        min_availability=0.9999,  # 99.99% availability (4 nines)
    ),
    window_minutes=1,
)

# Relaxed SLOs for non-critical endpoints
NON_CRITICAL_ENDPOINT_SLO = ServiceLevelObjective(
    name="non-critical-endpoints",
    description="SLO for non-critical endpoints (analytics, reporting, etc.)",
    latency=LatencySLI(
        p50_ms=100.0,
        p95_ms=500.0,
        p99_ms=2000.0,
        p999_ms=5000.0,
    ),
    error_rate=ErrorRateSLI(
        max_error_rate=0.05,  # Max 5% error rate
        max_5xx_rate=0.01,  # Max 1% 5xx errors
    ),
    throughput=ThroughputSLI(
        min_rps=10.0,
        max_rps=1000.0,
    ),
    availability=AvailabilitySLI(
        min_availability=0.99,  # 99% availability (2 nines)
    ),
    window_minutes=60,
)


def get_slo_for_endpoint(endpoint: str) -> ServiceLevelObjective:
    """
    Get the appropriate SLO for an endpoint.

    Args:
        endpoint: API endpoint path

    Returns:
        ServiceLevelObjective: The SLO for this endpoint
    """
    # Critical endpoints
    critical_patterns = [
        "/health",
        "/auth",
        "/login",
        "/payments",
        "/transactions",
    ]

    for pattern in critical_patterns:
        if pattern in endpoint:
            return CRITICAL_ENDPOINT_SLO

    # Non-critical endpoints
    non_critical_patterns = [
        "/analytics",
        "/reports",
        "/export",
        "/batch",
    ]

    for pattern in non_critical_patterns:
        if pattern in endpoint:
            return NON_CRITICAL_ENDPOINT_SLO

    # Default
    return ATLAS_API_SLO


def format_slo_summary(slo: ServiceLevelObjective) -> str:
    """
    Format SLO as human-readable summary.

    Args:
        slo: ServiceLevelObjective to format

    Returns:
        str: Formatted summary
    """
    return f"""
SLO: {slo.name}
Description: {slo.description}
Evaluation Window: {slo.window_minutes} minutes

Latency Targets:
  P50:   {slo.latency.p50_ms}ms
  P95:   {slo.latency.p95_ms}ms
  P99:   {slo.latency.p99_ms}ms
  P999:  {slo.latency.p999_ms}ms

Error Rate Targets:
  Max Error Rate: {slo.error_rate.max_error_rate * 100:.2f}%
  Max 5xx Rate:   {slo.error_rate.max_5xx_rate * 100:.2f}%

Throughput Targets:
  Min RPS: {slo.throughput.min_rps}
  Max RPS: {slo.throughput.max_rps}

Availability Target:
  Min Availability: {slo.availability.min_availability * 100:.2f}%
"""

